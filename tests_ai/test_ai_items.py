"""AI-generated (prompt P3): tests for tomlkit.items."""

import copy
import datetime as dt
import pickle

import pytest

import tomlkit
from tomlkit.exceptions import ConvertError, InvalidStringError
from tomlkit.items import (
    AoT,
    Array,
    Bool,
    Comment,
    Date,
    DateTime,
    DottedKey,
    Float,
    InlineTable,
    Integer,
    Key,
    SingleKey,
    String,
    StringType,
    Table,
    Time,
    Trivia,
    Whitespace,
    item,
)


class TestItemConversion:
    @pytest.mark.parametrize(
        "value,cls",
        [
            (True, Bool),
            (1, Integer),
            (1.5, Float),
            ("s", String),
            ([1, 2], Array),
            ((1, 2), Array),
            ({"a": 1}, Table),
            (dt.date(2020, 1, 2), Date),
            (dt.time(1, 2, 3), Time),
            (dt.datetime(2020, 1, 2, 3, 4, 5), DateTime),
        ],
    )
    def test_types(self, value, cls):
        assert isinstance(item(value), cls)

    def test_bool_is_not_integer(self):
        assert not isinstance(item(True), Integer)

    def test_item_passthrough(self):
        i = item(5)
        assert item(i) is i

    def test_list_of_dicts_is_aot(self):
        a = item([{"a": 1}, {"a": 2}])
        assert isinstance(a, AoT)
        assert len(a) == 2

    def test_list_of_dicts_inside_array_is_inline(self):
        a = item([[{"a": 1}]])
        assert isinstance(a, Array)
        assert isinstance(a[0][0], InlineTable)

    def test_dict_inside_array_becomes_inline_table(self):
        a = item([1, {"x": 1}])
        assert isinstance(a[1], InlineTable)
        assert a.as_string() == "[1, {x = 1}]"

    def test_empty_list(self):
        a = item([])
        assert isinstance(a, Array)
        assert a.as_string() == "[]"

    def test_unsupported(self):
        with pytest.raises(ConvertError):
            item(object())

    def test_none_unsupported(self):
        with pytest.raises(ConvertError):
            item(None)

    def test_utc_datetime_renders_z(self):
        d = item(dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc))
        assert d.as_string() == "2020-01-01T00:00:00Z"

    def test_sort_keys_puts_tables_last(self):
        t = item({"b": {"x": 1}, "a": 1, "c": 2}, _sort_keys=True)
        assert list(t.keys()) == ["a", "c", "b"]


class TestStringType:
    @pytest.mark.parametrize(
        "literal,multiline,expected",
        [
            (False, False, StringType.SLB),
            (False, True, StringType.MLB),
            (True, False, StringType.SLL),
            (True, True, StringType.MLL),
        ],
    )
    def test_select(self, literal, multiline, expected):
        assert StringType.select(literal, multiline) == expected

    def test_predicates(self):
        assert StringType.SLB.is_basic()
        assert StringType.SLL.is_literal()
        assert StringType.MLB.is_multiline()
        assert StringType.SLL.is_singleline()

    def test_toggle(self):
        # repair R1: toggle() flips single-line <-> multi-line, not basic <-> literal
        assert StringType.SLB.toggle() == StringType.MLB
        assert StringType.MLL.toggle() == StringType.SLL

    def test_unit(self):
        assert StringType.SLB.unit == '"'
        assert StringType.SLL.unit == "'"


class TestStringFromRaw:
    def test_basic(self):
        s = String.from_raw("hi")
        assert s == "hi"
        assert s.as_string() == '"hi"'

    def test_escapes_control_char(self):
        assert String.from_raw("\x01").as_string() == '"\\u0001"'

    def test_literal_rejects_newline(self):
        with pytest.raises(InvalidStringError):
            String.from_raw("a\nb", StringType.SLL)

    def test_multiline_literal_rejects_triple_quote(self):
        with pytest.raises(InvalidStringError):
            String.from_raw("a'''b", StringType.MLL)

    def test_multiline_leading_newline_preserved(self):
        s = String.from_raw("\nabc", StringType.MLB)
        doc = tomlkit.parse(f"a = {s.as_string()}")
        assert doc["a"] == "\nabc"

    def test_concat_keeps_type(self):
        s = tomlkit.string("ab", literal=True) + "cd"
        assert isinstance(s, String)
        assert s.as_string() == "'abcd'"

    def test_unwrap_is_plain_str(self):
        u = String.from_raw("x").unwrap()
        assert type(u) is str


class TestIntegerFloat:
    def test_integer_arithmetic_returns_integer(self):
        i = item(5)
        for r in (i + 1, i - 1, i * 2, i // 2, i % 2, -i, abs(i), i**2):
            assert isinstance(r, Integer)
        assert i + 1 == 6

    def test_integer_true_division_returns_float(self):
        r = item(5) / 2
        assert isinstance(r, Float)
        assert r == 2.5

    def test_integer_reflected(self):
        assert isinstance(1 + item(5), Integer)
        assert 10 - item(3) == 7

    def test_integer_bitwise(self):
        i = item(6)
        assert (i & 3) == 2
        assert (i | 1) == 7
        assert (i ^ 2) == 4
        assert (i << 1) == 12
        assert (i >> 1) == 3
        assert isinstance(~i, Integer)

    def test_integer_keeps_trivia_comment(self):
        doc = tomlkit.parse("a = 1 # c\n")
        doc["a"] += 1
        assert doc.as_string() == "a = 2 # c\n"

    def test_integer_unwrap(self):
        u = item(3).unwrap()
        assert type(u) is int

    def test_float_arithmetic(self):
        f = item(1.5)
        for r in (f + 1, f - 1, f * 2, f / 2, -f, abs(f)):
            assert isinstance(r, Float)
        assert f * 2 == 3.0

    def test_float_unwrap(self):
        assert type(item(1.5).unwrap()) is float

    def test_hash_matches_python(self):
        assert hash(item(5)) == hash(5)
        assert hash(item(1.5)) == hash(1.5)


class TestBool:
    def test_bool_behaviour(self):
        t, f = item(True), item(False)
        assert bool(t) is True
        assert bool(f) is False
        assert t == True  # noqa: E712
        assert t.as_string() == "true"
        assert f.as_string() == "false"
        assert t.unwrap() is True

    def test_hash(self):
        assert hash(item(True)) == hash(True)

    def test_pickle_bool_value(self):
        assert pickle.loads(pickle.dumps(item(True))).value is True


class TestDates:
    def test_date_add_sub(self):
        d = tomlkit.date("2020-01-31")
        assert isinstance(d + dt.timedelta(days=1), Date)
        assert d + dt.timedelta(days=1) == dt.date(2020, 2, 1)
        assert d - dt.timedelta(days=1) == dt.date(2020, 1, 30)
        assert d - dt.date(2020, 1, 1) == dt.timedelta(days=30)

    def test_date_replace(self):
        d = tomlkit.date("2020-01-31").replace(year=2021)
        assert isinstance(d, Date)
        assert d.as_string() == "2021-01-31"

    def test_datetime_add(self):
        d = tomlkit.datetime("2020-01-01T00:00:00Z")
        r = d + dt.timedelta(hours=1)
        assert isinstance(r, DateTime)
        assert r.hour == 1

    def test_datetime_sub_datetime(self):
        a = tomlkit.datetime("2020-01-02T00:00:00")
        b = tomlkit.datetime("2020-01-01T00:00:00")
        assert a - b == dt.timedelta(days=1)

    def test_datetime_astimezone(self):
        d = tomlkit.datetime("2020-01-01T00:00:00Z")
        r = d.astimezone(dt.timezone(dt.timedelta(hours=2)))
        assert isinstance(r, DateTime)
        assert r.hour == 2

    def test_time_replace(self):
        t = tomlkit.time("01:02:03").replace(hour=5)
        assert isinstance(t, Time)
        assert t.as_string() == "05:02:03"

    def test_unwrap_types(self):
        assert type(tomlkit.date("2020-01-01").unwrap()) is dt.date
        assert type(tomlkit.time("01:02:03").unwrap()) is dt.time
        assert type(tomlkit.datetime("2020-01-01T00:00:00").unwrap()) is dt.datetime


class TestArray:
    def test_append_and_render(self):
        a = tomlkit.array()
        a.append(1)
        a.append("x")
        assert a.as_string() == '[1, "x"]'

    def test_insert(self):
        a = tomlkit.array("[1, 3]")
        a.insert(1, 2)
        assert a == [1, 2, 3]
        assert a.as_string() == "[1, 2, 3]"

    def test_insert_negative(self):
        a = tomlkit.array("[1, 3]")
        a.insert(-1, 2)
        assert a == [1, 2, 3]

    def test_setitem(self):
        a = tomlkit.array("[1, 2, 3]")
        a[1] = 20
        assert a.as_string() == "[1, 20, 3]"

    def test_setitem_negative(self):
        a = tomlkit.array("[1, 2, 3]")
        a[-1] = 30
        assert a.as_string() == "[1, 2, 30]"

    def test_slice_assignment_rejected(self):
        a = tomlkit.array("[1, 2, 3]")
        with pytest.raises(ValueError):
            a[0:2] = [9, 9]
        assert a == [1, 2, 3]

    def test_delitem(self):
        a = tomlkit.array("[1, 2, 3]")
        del a[0]
        assert a == [2, 3]
        assert a.as_string() == "[2, 3]"

    def test_delitem_last(self):
        a = tomlkit.array("[1, 2, 3]")
        del a[-1]
        assert a.as_string() == "[1, 2]"

    def test_del_slice(self):
        a = tomlkit.array("[1, 2, 3, 4]")
        del a[1:3]
        assert a == [1, 4]

    def test_remove_and_pop(self):
        a = tomlkit.array("[1, 2, 3]")
        a.remove(2)
        assert a == [1, 3]
        assert a.pop() == 3
        assert a.as_string() == "[1]"

    def test_clear(self):
        a = tomlkit.array("[1, 2]")
        a.clear()
        assert a == []
        assert a.as_string() == "[]"

    def test_multiline(self):
        a = tomlkit.array("[1, 2]").multiline(True)
        assert a.as_string() == "[\n    1,\n    2,\n]"

    def test_add_line(self):
        a = tomlkit.array()
        a.add_line(1, 2, 3)
        a.add_line(4, 5, 6)
        a.add_line(indent="")
        assert a.as_string() == "[\n    1, 2, 3,\n    4, 5, 6,\n]"
        assert a == [1, 2, 3, 4, 5, 6]

    def test_add_line_with_comment(self):
        a = tomlkit.array()
        a.add_line(1, comment="first")
        a.add_line(indent="")
        assert "# first" in a.as_string()
        assert tomlkit.parse(f"a = {a.as_string()}")["a"] == [1]

    def test_add_line_comment_with_newline_rejected(self):
        a = tomlkit.array()
        with pytest.raises(ValueError):
            a.add_line(1, comment="bad\ncomment")

    def test_unwrap(self):
        u = tomlkit.array("[1, [2]]").unwrap()
        assert u == [1, [2]]
        assert type(u) is list
        assert type(u[1]) is list

    def test_copy(self):
        a = tomlkit.array("[1, 2]")
        b = copy.copy(a)
        b.append(3)
        assert a == [1, 2]

    def test_extend(self):
        a = tomlkit.array("[1]")
        a.extend([2, 3])
        assert a.as_string() == "[1, 2, 3]"


class TestTable:
    def test_append_and_getitem(self):
        t = tomlkit.table()
        t.append("a", 1)
        assert t["a"] == 1
        assert "a" in t

    def test_add_is_append(self):
        t = tomlkit.table()
        t.add("a", 1)
        assert t.as_string() == "a = 1\n"

    def test_remove(self):
        t = tomlkit.table()
        t.add("a", 1).add("b", 2)
        t.remove("a")
        assert "a" not in t
        assert t.as_string() == "b = 2\n"

    def test_delitem(self):
        t = tomlkit.table()
        t["a"] = 1
        del t["a"]
        assert len(t) == 0

    def test_setdefault(self):
        t = tomlkit.table()
        assert t.setdefault("a", 1) == 1
        assert t.setdefault("a", 2) == 1

    def test_unwrap_nested(self):
        t = item({"a": {"b": [1, 2]}})
        u = t.unwrap()
        assert u == {"a": {"b": [1, 2]}}
        assert type(u["a"]) is dict

    def test_is_super_table(self):
        assert tomlkit.table(True).is_super_table()
        assert not tomlkit.table(False).is_super_table()

    def test_indent(self):
        doc = tomlkit.document()
        t = tomlkit.table()
        t["x"] = 1
        t.indent(2)
        doc["t"] = t
        assert "  x = 1" in doc.as_string()

    def test_iteration_and_len(self):
        t = item({"a": 1, "b": 2})
        assert list(t) == ["a", "b"]
        assert len(t) == 2

    def test_copy_independent(self):
        t = item({"a": 1})
        c = t.copy()
        c["a"] = 2
        assert t["a"] == 1


class TestInlineTable:
    def test_render(self):
        t = tomlkit.inline_table()
        t["a"] = 1
        t["b"] = "x"
        assert t.as_string() == '{a = 1, b = "x"}'

    def test_remove(self):
        t = tomlkit.inline_table()
        t.update({"a": 1, "b": 2})
        del t["a"]
        assert t.as_string() == "{b = 2}"

    def test_nested_dict_becomes_inline(self):
        t = tomlkit.inline_table()
        t["n"] = {"x": 1}
        assert isinstance(t["n"], InlineTable)
        assert t.as_string() == "{n = {x = 1}}"

    def test_in_document(self):
        doc = tomlkit.document()
        t = tomlkit.inline_table()
        t["a"] = 1
        doc["t"] = t
        assert doc.as_string() == "t = {a = 1}\n"


class TestAoT:
    def test_append_dict(self):
        a = tomlkit.aot()
        a.append({"x": 1})
        assert isinstance(a[0], Table)
        assert a.unwrap() == [{"x": 1}]

    def test_in_document(self):
        doc = tomlkit.document()
        doc["p"] = [{"n": 1}, {"n": 2}]
        assert doc.as_string() == "[[p]]\nn = 1\n\n[[p]]\nn = 2\n"

    def test_delete_element(self):
        doc = tomlkit.parse("[[p]]\nn = 1\n\n[[p]]\nn = 2\n")
        del doc["p"][0]
        assert doc.unwrap() == {"p": [{"n": 2}]}


class TestKeys:
    def test_bare(self):
        assert SingleKey("abc").is_bare()
        assert not SingleKey("a b").is_bare()

    def test_equality_and_hash(self):
        assert SingleKey("a") == "a"
        assert SingleKey("a") == SingleKey("a")
        assert hash(SingleKey("a")) == hash("a")

    def test_concat(self):
        k = SingleKey("a").concat(SingleKey("b"))
        assert isinstance(k, DottedKey)
        assert k.as_string() == "a.b"
        # repair R2: is_dotted() is parser state ('followed by other keys'); use is_multi()
        assert k.is_multi()

    def test_dotted_iter(self):
        k = tomlkit.key(["a", "b", "c"])
        assert [str(p) for p in k] == ["a", "b", "c"]

    def test_quoted_rendering(self):
        assert SingleKey("a.b").as_string() == '"a.b"'
        assert SingleKey("").as_string() == '""'


class TestItemDecorations:
    def test_comment(self):
        doc = tomlkit.document()
        doc["a"] = item(1).comment("note")
        assert doc.as_string() == "a = 1 # note\n"

    def test_comment_adds_hash(self):
        i = item(1).comment("# already")
        assert i.trivia.comment == "# already"

    def test_comment_rejects_newline(self):
        with pytest.raises(ValueError):
            item(1).comment("a\nb")

    def test_indent(self):
        doc = tomlkit.document()
        doc["a"] = item(1).indent(4)
        assert doc.as_string() == "    a = 1\n"

    def test_type_predicates(self):
        assert item(True).is_boolean()
        assert item({"a": 1}).is_table()
        assert tomlkit.inline_table().is_inline_table()
        assert tomlkit.aot().is_aot()


class TestPickle:
    @pytest.mark.xfail(strict=True, reason="DEFECT D2: Bool.__eq__ returns NotImplemented for another Bool, so item(True) != item(True)")
    def test_bool_equals_bool(self):
        assert item(True) == item(True)

    @pytest.mark.parametrize(
        "obj",
        [
            item(1),
            item(1.5),
            item("s"),
            tomlkit.date("2020-01-01"),
            tomlkit.array("[1, 2]"),
        ],
    )
    def test_round_trip(self, obj):
        assert pickle.loads(pickle.dumps(obj)) == obj

    def test_document(self):
        doc = tomlkit.parse("a = 1 # c\n[t]\nx = 'y'\n")
        assert pickle.loads(pickle.dumps(doc)).as_string() == doc.as_string()


class TestWhitespaceComment:
    def test_whitespace(self):
        w = Whitespace("  ")
        assert w.s == "  "
        assert w.value == "  "
        assert not w.is_fixed()

    def test_comment_item(self):
        c = Comment(Trivia(comment="# x"))
        assert "# x" in c.as_string()
