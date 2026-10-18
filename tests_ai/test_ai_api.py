"""AI-generated (prompt P1): tests for the public tomlkit API."""

import datetime as dt
import io

import pytest

import tomlkit
from tomlkit.exceptions import ConvertError, ParseError, UnexpectedCharError
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
    SingleKey,
    String,
    StringType,
    Table,
    Time,
    Whitespace,
)
from tomlkit.toml_document import TOMLDocument


SAMPLE = """\
# This is a TOML document.

title = "TOML Example"

[owner]
name = "Tom Preston-Werner"  # inline comment
dob = 1979-05-27T07:32:00-08:00

[database]
ports = [ 8000, 8001, 8002 ]
enabled = true
"""


class TestParseAndLoads:
    def test_parse_returns_document(self):
        doc = tomlkit.parse(SAMPLE)
        assert isinstance(doc, TOMLDocument)

    def test_parse_values(self):
        doc = tomlkit.parse(SAMPLE)
        assert doc["title"] == "TOML Example"
        assert doc["owner"]["name"] == "Tom Preston-Werner"
        assert doc["database"]["ports"] == [8000, 8001, 8002]
        assert doc["database"]["enabled"] is True

    def test_loads_is_alias_of_parse(self):
        assert tomlkit.loads(SAMPLE) == tomlkit.parse(SAMPLE)

    def test_parse_accepts_bytes(self):
        doc = tomlkit.parse(b'a = "b"')
        assert doc["a"] == "b"

    def test_parse_empty_string(self):
        doc = tomlkit.parse("")
        assert len(doc) == 0
        assert doc.as_string() == ""

    def test_parse_invalid_raises(self):
        with pytest.raises(ParseError):
            tomlkit.parse("a = ")


class TestRoundTrip:
    def test_round_trip_identical(self):
        assert tomlkit.dumps(tomlkit.parse(SAMPLE)) == SAMPLE

    @pytest.mark.parametrize(
        "src",
        [
            "a = 1\n",
            "a = 1 # comment\n",
            "[t]\n  x = 'y'\n",
            "arr = [\n  1,\n  2,\n]\n",
            'inline = { a = 1, b = "two" }\n',
            "[[aot]]\nx = 1\n\n[[aot]]\nx = 2\n",
            "\n\n# only comments\n\n",
        ],
    )
    def test_round_trip_preserves_formatting(self, src):
        assert tomlkit.dumps(tomlkit.parse(src)) == src


class TestDumps:
    def test_dumps_plain_dict(self):
        assert tomlkit.dumps({"a": 1, "b": "x"}) == 'a = 1\nb = "x"\n'

    def test_dumps_nested_dict_creates_table(self):
        out = tomlkit.dumps({"t": {"x": 1}})
        assert out == "[t]\nx = 1\n"

    def test_dumps_sort_keys(self):
        out = tomlkit.dumps({"b": 1, "a": 2}, sort_keys=True)
        assert out == "a = 2\nb = 1\n"

    def test_dumps_sort_keys_on_document(self):
        doc = tomlkit.parse("b = 1\na = 2\n")
        out = tomlkit.dumps(doc, sort_keys=True)
        assert out.index("a = 2") < out.index("b = 1")

    def test_dumps_rejects_non_mapping(self):
        with pytest.raises(TypeError):
            tomlkit.dumps([1, 2, 3])

    def test_dumps_table_item(self):
        t = tomlkit.table()
        t["x"] = 1
        assert tomlkit.dumps(t) == "x = 1\n"


class TestFileLikeIO:
    def test_load_from_text_stream(self):
        doc = tomlkit.load(io.StringIO("a = 1\n"))
        assert doc["a"] == 1

    def test_load_from_bytes_stream(self):
        doc = tomlkit.load(io.BytesIO(b"a = 1\n"))
        assert doc["a"] == 1

    def test_dump_to_stream(self):
        buf = io.StringIO()
        tomlkit.dump({"a": 1}, buf)
        assert buf.getvalue() == "a = 1\n"

    def test_dump_sort_keys(self):
        buf = io.StringIO()
        tomlkit.dump({"z": 1, "a": 2}, buf, sort_keys=True)
        assert buf.getvalue() == "a = 2\nz = 1\n"


class TestDocument:
    def test_document_empty(self):
        doc = tomlkit.document()
        assert isinstance(doc, TOMLDocument)
        assert doc.as_string() == ""

    def test_document_build(self):
        doc = tomlkit.document()
        doc.add("title", "x")
        doc.add(tomlkit.nl())
        doc["n"] = 3
        assert doc.as_string() == 'title = "x"\n\nn = 3\n'


class TestScalarFactories:
    @pytest.mark.parametrize("raw,expected", [(5, 5), ("42", 42), ("-7", -7)])
    def test_integer(self, raw, expected):
        i = tomlkit.integer(raw)
        assert isinstance(i, Integer)
        assert i == expected

    def test_integer_invalid(self):
        with pytest.raises(ValueError):
            tomlkit.integer("abc")

    @pytest.mark.parametrize("raw,expected", [(1.5, 1.5), ("3.25", 3.25)])
    def test_float(self, raw, expected):
        f = tomlkit.float_(raw)
        assert isinstance(f, Float)
        assert f == expected

    def test_float_invalid(self):
        with pytest.raises(ValueError):
            tomlkit.float_("x.y")

    @pytest.mark.parametrize(
        "raw,expected", [("true", True), ("false", False), (True, True), (False, False)]
    )
    def test_boolean(self, raw, expected):
        b = tomlkit.boolean(raw)
        assert isinstance(b, Bool)
        assert b.value is expected

    def test_boolean_other_string_is_false(self):
        assert tomlkit.boolean("yes").value is False


class TestStringFactory:
    def test_basic_default(self):
        s = tomlkit.string("hello")
        assert isinstance(s, String)
        assert s.as_string() == '"hello"'
        assert s.type == StringType.SLB

    def test_literal(self):
        assert tomlkit.string("C:\\path", literal=True).as_string() == "'C:\\path'"

    def test_multiline_basic(self):
        s = tomlkit.string("a\nb", multiline=True)
        assert s.as_string() == '"""a\nb"""'

    def test_multiline_literal(self):
        s = tomlkit.string("a\nb", literal=True, multiline=True)
        assert s.as_string() == "'''a\nb'''"

    def test_basic_escapes(self):
        assert tomlkit.string('a"b\\c\n').as_string() == '"a\\"b\\\\c\\n"'

    def test_no_escape(self):
        assert tomlkit.string("a\\tb", escape=False).as_string() == '"a\\tb"'

    def test_literal_cannot_contain_quote(self):
        with pytest.raises(ValueError):
            tomlkit.string("it's", literal=True)


class TestDateTimeFactories:
    def test_date(self):
        d = tomlkit.date("1979-05-27")
        assert isinstance(d, Date)
        assert d == dt.date(1979, 5, 27)

    @pytest.mark.xfail(strict=True, reason="DEFECT D1: date() accepts datetime strings (datetime is a date subclass)")
    def test_date_rejects_datetime(self):
        with pytest.raises(ValueError):
            tomlkit.date("1979-05-27T07:32:00")

    def test_time(self):
        t = tomlkit.time("07:32:00")
        assert isinstance(t, Time)
        assert t == dt.time(7, 32)

    def test_time_rejects_date(self):
        with pytest.raises(ValueError):
            tomlkit.time("1979-05-27")

    def test_datetime_with_offset(self):
        d = tomlkit.datetime("1979-05-27T07:32:00-08:00")
        assert isinstance(d, DateTime)
        assert d.utcoffset() == dt.timedelta(hours=-8)

    def test_datetime_rejects_time(self):
        with pytest.raises(ValueError):
            tomlkit.datetime("07:32:00")

    def test_invalid_string(self):
        with pytest.raises(ValueError):
            tomlkit.datetime("not a date")


class TestContainerFactories:
    def test_array_default_empty(self):
        a = tomlkit.array()
        assert isinstance(a, Array)
        assert a == []

    def test_array_from_string(self):
        assert tomlkit.array("[1, 2, 3]") == [1, 2, 3]

    def test_array_rejects_non_array(self):
        with pytest.raises(ValueError):
            tomlkit.array("1")

    def test_table(self):
        t = tomlkit.table()
        assert isinstance(t, Table)
        assert len(t) == 0

    def test_super_table_renders_dotted_header(self):
        doc = tomlkit.document()
        foo = tomlkit.table(True)
        bar = tomlkit.table()
        bar.update({"x": 1})
        foo.append("bar", bar)
        doc.append("foo", foo)
        assert doc.as_string() == "[foo.bar]\nx = 1\n"

    def test_inline_table(self):
        t = tomlkit.inline_table()
        t.update({"x": 1, "y": 2})
        assert isinstance(t, InlineTable)
        assert t.as_string() == "{x = 1, y = 2}"

    def test_aot(self):
        doc = tomlkit.document()
        a = tomlkit.aot()
        a.append(tomlkit.item({"x": 1}))
        doc.append("foo", a)
        assert isinstance(a, AoT)
        assert doc.as_string() == "[[foo]]\nx = 1\n"


class TestKeyFactory:
    def test_single_key(self):
        k = tomlkit.key("foo")
        assert isinstance(k, SingleKey)
        assert k.as_string() == "foo"

    def test_dotted_key(self):
        k = tomlkit.key(["bar", "baz"])
        assert isinstance(k, DottedKey)
        assert k.as_string() == "bar.baz"

    def test_list_of_one_is_single_key(self):
        assert isinstance(tomlkit.key(["only"]), SingleKey)

    def test_key_needing_quotes(self):
        assert tomlkit.key("a b").as_string() == '"a b"'

    def test_keys_in_document(self):
        doc = tomlkit.document()
        doc.append(tomlkit.key("foo"), 1)
        doc.append(tomlkit.key(["bar", "baz"]), 2)
        assert doc.as_string() == "foo = 1\nbar.baz = 2\n"


class TestValueAndKeyValue:
    @pytest.mark.parametrize(
        "raw,expected",
        [("1", 1), ("true", True), ("[1, 2, 3]", [1, 2, 3]), ('"s"', "s"), ("1.5", 1.5)],
    )
    def test_value(self, raw, expected):
        assert tomlkit.value(raw) == expected

    def test_value_trailing_garbage(self):
        with pytest.raises(UnexpectedCharError):
            tomlkit.value("1 2")

    def test_key_value(self):
        k, v = tomlkit.key_value("foo = 1")
        assert k == SingleKey("foo")
        assert v == 1

    def test_key_value_invalid(self):
        with pytest.raises(ParseError):
            tomlkit.key_value("= 1")


class TestTriviaFactories:
    def test_ws(self):
        w = tomlkit.ws("   ")
        assert isinstance(w, Whitespace)
        assert w.as_string() == "   "
        assert w.is_fixed()

    def test_nl(self):
        assert tomlkit.nl().as_string() == "\n"

    def test_comment(self):
        c = tomlkit.comment("hello")
        assert isinstance(c, Comment)
        assert c.as_string().strip() == "# hello"

    def test_multiline_comment(self):
        doc = tomlkit.document()
        doc.add(tomlkit.comment("one\ntwo"))
        out = doc.as_string()
        assert "# one\n" in out
        assert "# two" in out
        # still valid TOML
        tomlkit.parse(out)


class _Point:
    def __init__(self, x, y):
        self.x, self.y = x, y


class TestEncoders:
    def test_unsupported_type_raises(self):
        with pytest.raises(ConvertError):
            tomlkit.item(_Point(1, 2))

    def test_register_and_unregister(self):
        def encode_point(obj):
            if isinstance(obj, _Point):
                return tomlkit.item([obj.x, obj.y])
            raise ConvertError("not a point")

        tomlkit.register_encoder(encode_point)
        try:
            assert tomlkit.item(_Point(1, 2)) == [1, 2]
            assert tomlkit.dumps({"p": _Point(3, 4)}) == "p = [3, 4]\n"
        finally:
            tomlkit.unregister_encoder(encode_point)
        with pytest.raises(ConvertError):
            tomlkit.item(_Point(1, 2))

    def test_encoder_with_kwargs(self):
        seen = {}

        def enc(obj, _parent=None, _sort_keys=False):
            if isinstance(obj, _Point):
                seen["sort"] = _sort_keys
                return tomlkit.item(obj.x)
            raise ConvertError("no")

        tomlkit.register_encoder(enc)
        try:
            tomlkit.item(_Point(9, 9), _sort_keys=True)
            assert seen["sort"] is True
        finally:
            tomlkit.unregister_encoder(enc)

    def test_encoder_must_return_item(self):
        def bad(obj):
            return 123

        tomlkit.register_encoder(bad)
        try:
            with pytest.raises(ConvertError):
                tomlkit.item(_Point(1, 1))
        finally:
            tomlkit.unregister_encoder(bad)

    def test_unregister_unknown_is_noop(self):
        tomlkit.unregister_encoder(lambda o: o)  # should not raise
