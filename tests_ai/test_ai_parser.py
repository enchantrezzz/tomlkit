"""AI-generated (prompt P2): parser behaviour via tomlkit.parse."""

import datetime as dt
import math

import pytest

import tomlkit
from tomlkit.exceptions import (
    EmptyKeyError,
    InvalidCharInStringError,
    InvalidControlChar,
    InvalidNumberError,
    KeyAlreadyPresent,
    ParseError,
    UnexpectedCharError,
    UnexpectedEofError,
)
from tomlkit.items import AoT, Array, InlineTable, Table


class TestKeys:
    def test_bare_key(self):
        assert tomlkit.parse("key = 1")["key"] == 1

    def test_bare_key_with_dash_and_underscore(self):
        assert tomlkit.parse("bare-key_1 = 1")["bare-key_1"] == 1

    def test_quoted_basic_key(self):
        assert tomlkit.parse('"a b" = 1')["a b"] == 1

    def test_quoted_literal_key(self):
        assert tomlkit.parse("'a.b' = 1")["a.b"] == 1

    def test_empty_quoted_key(self):
        assert tomlkit.parse('"" = 1')[""] == 1

    def test_dotted_key_creates_tables(self):
        doc = tomlkit.parse("a.b.c = 1")
        assert doc["a"]["b"]["c"] == 1
        assert doc.unwrap() == {"a": {"b": {"c": 1}}}

    def test_dotted_key_with_whitespace(self):
        doc = tomlkit.parse("a . b = 1")
        assert doc["a"]["b"] == 1

    def test_missing_key(self):
        with pytest.raises(EmptyKeyError):
            tomlkit.parse("= 1")

    def test_duplicate_key(self):
        # repair R3: top-level duplicates are wrapped in ParseError with a position
        with pytest.raises(ParseError, match="already exists"):
            tomlkit.parse("a = 1\na = 2")

    def test_missing_equals(self):
        with pytest.raises(ParseError):
            tomlkit.parse("a 1")


class TestStrings:
    @pytest.mark.parametrize(
        "src,expected",
        [
            (r'a = "tab\tnew\nquote\"back\\"', 'tab\tnew\nquote"back\\'),
            (r'a = "\u00e9\U0001F600"', "é\U0001f600"),
            ("a = 'C:\\Users\\x'", "C:\\Users\\x"),
            ('a = """\nline1\nline2"""', "line1\nline2"),
            ("a = '''\nraw\\n'''", "raw\\n"),
            ('a = """one \\\n    two"""', "one two"),
            ('a = ""', ""),
        ],
    )
    def test_string_values(self, src, expected):
        assert tomlkit.parse(src)["a"] == expected

    def test_multiline_allows_quotes_inside(self):
        assert tomlkit.parse('a = """he said "hi" ok"""')["a"] == 'he said "hi" ok'

    def test_unterminated_basic_string(self):
        with pytest.raises(ParseError):
            tomlkit.parse('a = "abc')

    def test_unterminated_multiline_string(self):
        with pytest.raises(ParseError):
            tomlkit.parse('a = """abc')

    def test_newline_in_basic_string(self):
        with pytest.raises(ParseError):
            tomlkit.parse('a = "ab\ncd"')

    def test_invalid_escape(self):
        with pytest.raises(ParseError):
            tomlkit.parse(r'a = "\q"')

    def test_invalid_unicode_escape(self):
        with pytest.raises(ParseError):
            tomlkit.parse(r'a = "\uD800"')

    def test_control_char_rejected(self):
        with pytest.raises(InvalidControlChar):
            tomlkit.parse('a = "x\x01y"')


class TestIntegers:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("99", 99),
            ("+17", 17),
            ("-17", -17),
            ("0", 0),
            ("1_000_000", 1000000),
            ("0xDEADbeef", 0xDEADBEEF),
            ("0o755", 0o755),
            ("0b1101", 0b1101),
        ],
    )
    def test_valid(self, raw, expected):
        assert tomlkit.parse(f"a = {raw}")["a"] == expected

    def test_preserves_raw_representation(self):
        assert tomlkit.dumps(tomlkit.parse("a = 0xff\n")) == "a = 0xff\n"

    @pytest.mark.parametrize("raw", ["01", "1__0", "_1", "1_", "0x", "0b2", "+0x1"])
    def test_invalid(self, raw):
        with pytest.raises(ParseError):
            tomlkit.parse(f"a = {raw}")


class TestFloats:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("3.1415", 3.1415),
            ("-0.01", -0.01),
            ("5e+22", 5e22),
            ("1e06", 1e6),
            ("-2E-2", -0.02),
            ("6.626e-34", 6.626e-34),
            ("224_617.445_991", 224617.445991),
        ],
    )
    def test_valid(self, raw, expected):
        assert tomlkit.parse(f"a = {raw}")["a"] == pytest.approx(expected)

    @pytest.mark.parametrize("raw,sign", [("inf", 1), ("+inf", 1), ("-inf", -1)])
    def test_inf(self, raw, sign):
        v = tomlkit.parse(f"a = {raw}")["a"]
        assert math.isinf(v)
        assert math.copysign(1, v) == sign

    @pytest.mark.parametrize("raw", ["nan", "+nan", "-nan"])
    def test_nan(self, raw):
        assert math.isnan(tomlkit.parse(f"a = {raw}")["a"])

    @pytest.mark.parametrize("raw", [".5", "5.", "1.e5", "1e", "1.2.3"])
    def test_invalid(self, raw):
        with pytest.raises(ParseError):
            tomlkit.parse(f"a = {raw}")


class TestBooleans:
    def test_true_false(self):
        doc = tomlkit.parse("t = true\nf = false")
        assert doc["t"] is True
        assert doc["f"] is False

    @pytest.mark.parametrize("raw", ["True", "FALSE", "tru"])
    def test_invalid(self, raw):
        with pytest.raises(ParseError):
            tomlkit.parse(f"a = {raw}")


class TestDates:
    def test_offset_datetime_z(self):
        v = tomlkit.parse("a = 1979-05-27T07:32:00Z")["a"]
        assert v == dt.datetime(1979, 5, 27, 7, 32, tzinfo=dt.timezone.utc)

    def test_offset_datetime_negative(self):
        v = tomlkit.parse("a = 1979-05-27T00:32:00.999999-07:00")["a"]
        assert v.microsecond == 999999
        assert v.utcoffset() == dt.timedelta(hours=-7)

    def test_space_separator(self):
        v = tomlkit.parse("a = 1979-05-27 07:32:00Z")["a"]
        assert v.hour == 7

    def test_local_datetime(self):
        v = tomlkit.parse("a = 1979-05-27T07:32:00")["a"]
        assert v.tzinfo is None

    def test_local_date(self):
        assert tomlkit.parse("a = 1979-05-27")["a"] == dt.date(1979, 5, 27)

    def test_local_time(self):
        assert tomlkit.parse("a = 07:32:00")["a"] == dt.time(7, 32)

    def test_time_fraction(self):
        assert tomlkit.parse("a = 00:32:00.5")["a"].microsecond == 500000

    def test_time_without_seconds(self):
        # TOML 1.1 allows omitting seconds
        assert tomlkit.parse("a = 07:32")["a"] == dt.time(7, 32)

    @pytest.mark.parametrize(
        "raw", ["1979-13-01", "1979-02-30", "1979-05-27T25:00:00", "07:60:00"]
    )
    def test_invalid(self, raw):
        with pytest.raises(ParseError):
            tomlkit.parse(f"a = {raw}")


class TestArrays:
    def test_simple(self):
        a = tomlkit.parse("a = [1, 2, 3]")["a"]
        assert isinstance(a, Array)
        assert a == [1, 2, 3]

    def test_empty(self):
        assert tomlkit.parse("a = []")["a"] == []

    def test_nested(self):
        assert tomlkit.parse("a = [[1, 2], ['x']]")["a"] == [[1, 2], ["x"]]

    def test_mixed_types_allowed(self):
        assert tomlkit.parse('a = [1, "a", 2.5]')["a"] == [1, "a", 2.5]

    def test_multiline_trailing_comma_and_comments(self):
        src = "a = [\n  1, # one\n  2,\n]\n"
        doc = tomlkit.parse(src)
        assert doc["a"] == [1, 2]
        assert tomlkit.dumps(doc) == src

    def test_missing_comma(self):
        with pytest.raises(ParseError):
            tomlkit.parse("a = [1 2]")

    def test_unclosed(self):
        with pytest.raises(ParseError):
            tomlkit.parse("a = [1, 2")

    def test_leading_comma(self):
        with pytest.raises(ParseError):
            tomlkit.parse("a = [,1]")


class TestInlineTables:
    def test_simple(self):
        t = tomlkit.parse('a = { x = 1, y = "z" }')["a"]
        assert isinstance(t, InlineTable)
        assert t == {"x": 1, "y": "z"}

    def test_empty(self):
        assert tomlkit.parse("a = {}")["a"] == {}

    def test_nested_and_dotted(self):
        t = tomlkit.parse("a = { b.c = 1, d = { e = 2 } }")["a"]
        assert t.unwrap() == {"b": {"c": 1}, "d": {"e": 2}}

    def test_multiline_inline_table_toml11(self):
        # TOML 1.1 allows newlines and trailing commas inside inline tables
        t = tomlkit.parse("a = {\n  x = 1,\n  y = 2,\n}")["a"]
        assert t == {"x": 1, "y": 2}

    @pytest.mark.xfail(strict=True, raises=KeyAlreadyPresent, reason="DEFECT D3: inline-table duplicate raises bare KeyAlreadyPresent, not ParseError")
    def test_duplicate_key_in_inline(self):
        with pytest.raises(ParseError):
            tomlkit.parse("a = { x = 1, x = 2 }")

    def test_unclosed(self):
        with pytest.raises(ParseError):
            tomlkit.parse("a = { x = 1")


class TestTables:
    def test_standard_table(self):
        doc = tomlkit.parse("[t]\nx = 1\n")
        assert isinstance(doc["t"], Table)
        assert doc["t"]["x"] == 1

    def test_dotted_header(self):
        doc = tomlkit.parse("[a.b.c]\nx = 1\n")
        assert doc["a"]["b"]["c"]["x"] == 1

    def test_quoted_header(self):
        doc = tomlkit.parse('[ "a b" . c ]\nx = 1\n')
        assert doc["a b"]["c"]["x"] == 1

    def test_super_table_defined_later(self):
        doc = tomlkit.parse("[a.b]\nx = 1\n[a]\ny = 2\n")
        assert doc.unwrap() == {"a": {"b": {"x": 1}, "y": 2}}

    def test_redefined_table(self):
        with pytest.raises(ParseError):
            tomlkit.parse("[a]\nx = 1\n[a]\ny = 2\n")

    def test_empty_header(self):
        with pytest.raises(ParseError):
            tomlkit.parse("[]\n")

    def test_unclosed_header(self):
        with pytest.raises(ParseError):
            tomlkit.parse("[a\nx = 1\n")

    def test_out_of_order_tables_round_trip(self):
        src = "[a.x]\n1 = 1\n\n[b]\n2 = 2\n\n[a.y]\n3 = 3\n"
        doc = tomlkit.parse(src)
        assert doc["a"]["x"]["1"] == 1
        assert doc["a"]["y"]["3"] == 3
        assert tomlkit.dumps(doc) == src


class TestArrayOfTables:
    def test_aot(self):
        src = '[[p]]\nname = "a"\n\n[[p]]\nname = "b"\n'
        doc = tomlkit.parse(src)
        assert isinstance(doc["p"], AoT)
        assert [t["name"] for t in doc["p"]] == ["a", "b"]

    def test_nested_aot(self):
        src = "[[f]]\nn = 1\n[[f.v]]\nc = 'r'\n[[f]]\nn = 2\n"
        doc = tomlkit.parse(src)
        assert doc.unwrap() == {"f": [{"n": 1, "v": [{"c": "r"}]}, {"n": 2}]}

    def test_static_array_then_aot_conflict(self):
        with pytest.raises(ParseError):
            tomlkit.parse("a = [1]\n[[a]]\n")


class TestComments:
    def test_full_line_and_trailing(self):
        doc = tomlkit.parse("# top\na = 1 # trailing\n")
        assert doc["a"] == 1
        assert doc["a"].trivia.comment == "# trailing"

    def test_hash_in_string_is_not_comment(self):
        assert tomlkit.parse('a = "x # y"')["a"] == "x # y"

    def test_control_char_in_comment(self):
        with pytest.raises(ParseError):
            tomlkit.parse("# bad \x00 comment\n")


class TestErrorPositions:
    def test_line_and_col(self):
        with pytest.raises(ParseError) as exc:
            tomlkit.parse("a = 1\nb = 2\nc = @\n")
        assert exc.value.line == 3
        assert exc.value.col >= 4

    def test_message_contains_position(self):
        with pytest.raises(ParseError) as exc:
            tomlkit.parse("a = @")
        assert "line 1" in str(exc.value)

    def test_eof_in_value(self):
        with pytest.raises((UnexpectedEofError, ParseError)):
            tomlkit.parse("a =")


class TestWhitespaceAndNewlines:
    def test_crlf_newlines(self):
        doc = tomlkit.parse("a = 1\r\nb = 2\r\n")
        assert doc["b"] == 2
        assert tomlkit.dumps(doc) == "a = 1\r\nb = 2\r\n"

    def test_tabs_as_whitespace(self):
        assert tomlkit.parse("a\t=\t1")["a"] == 1

    def test_bare_cr_rejected(self):
        with pytest.raises(ParseError):
            tomlkit.parse("a = 1\rb = 2")
