"""AI-generated (prompt P5): _utils, source and exceptions."""

import datetime as dt

import pytest

from tomlkit._utils import escape_string, merge_dicts, parse_rfc3339
from tomlkit.exceptions import (
    EmptyKeyError,
    InvalidControlChar,
    InvalidStringError,
    KeyAlreadyPresent,
    MixedArrayTypesError,
    NonExistentKey,
    ParseError,
    TOMLKitError,
    UnexpectedCharError,
    UnexpectedEofError,
)
from tomlkit.source import Source


class TestParseRfc3339:
    def test_datetime_z(self):
        assert parse_rfc3339("1979-05-27T07:32:00Z") == dt.datetime(
            1979, 5, 27, 7, 32, tzinfo=dt.timezone.utc
        )

    def test_datetime_lowercase(self):
        v = parse_rfc3339("1979-05-27t07:32:00z")
        assert v.tzinfo is not None

    def test_datetime_positive_offset(self):
        v = parse_rfc3339("1979-05-27T07:32:00+05:30")
        assert v.utcoffset() == dt.timedelta(hours=5, minutes=30)

    def test_datetime_negative_offset(self):
        v = parse_rfc3339("1979-05-27T07:32:00-08:00")
        assert v.utcoffset() == dt.timedelta(hours=-8)

    def test_datetime_no_seconds(self):
        assert parse_rfc3339("1979-05-27T07:32") == dt.datetime(1979, 5, 27, 7, 32)

    @pytest.mark.parametrize(
        "frac,us", [("1", 100000), ("123456", 123456), ("1234567", 123456)]
    )
    def test_fraction_padding_and_truncation(self, frac, us):
        v = parse_rfc3339(f"1979-05-27T07:32:00.{frac}")
        assert v.microsecond == us

    def test_date(self):
        assert parse_rfc3339("2000-02-29") == dt.date(2000, 2, 29)

    def test_time(self):
        assert parse_rfc3339("07:32:00.5") == dt.time(7, 32, 0, 500000)

    @pytest.mark.parametrize(
        "bad", ["", "2000-13-01", "25:00:00", "1979-05-27X07:32:00", "abc"]
    )
    def test_invalid(self, bad):
        with pytest.raises(ValueError):
            parse_rfc3339(bad)

    def test_invalid_calendar_date(self):
        with pytest.raises(ValueError):
            parse_rfc3339("2001-02-29")


class TestEscapeString:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("plain", "plain"),
            ('a"b', 'a\\"b'),
            ("a\\b", "a\\\\b"),
            ("\n\t\r", "\\n\\t\\r"),
            ("\b\f", "\\b\\f"),
            ("\x1b", "\\e"),
            ("\x00", "\\u0000"),
            ("\x7f", "\\u007f"),
        ],
    )
    def test_basic(self, raw, expected):
        assert escape_string(raw) == expected

    def test_custom_sequences(self):
        assert escape_string('a"""b', {'"""'}) == 'a""\\"b'

    def test_bytes_input(self):
        assert escape_string(b"x\n") == "x\\n"


class TestMergeDicts:
    def test_merge_nested(self):
        d1 = {"a": {"x": 1}, "b": 1}
        merge_dicts(d1, {"a": {"y": 2}, "c": 3})
        assert d1 == {"a": {"x": 1, "y": 2}, "b": 1, "c": 3}

    def test_overwrite_scalar(self):
        d1 = {"a": 1}
        merge_dicts(d1, {"a": {"x": 1}})
        assert d1 == {"a": {"x": 1}}


class TestSource:
    def test_initial_state(self):
        s = Source("abc")
        assert s.current == "a"
        assert s.idx == 0
        assert not s.end()

    def test_inc_until_end(self):
        s = Source("ab")
        assert s.inc() is True
        assert s.current == "b"
        assert s.inc() is False
        assert s.end()
        assert s.current == Source.EOF

    def test_inc_raises_when_asked(self):
        # repair R4: exception class must take (line, col) only
        s = Source("a")
        with pytest.raises(UnexpectedEofError):
            s.inc(exception=UnexpectedEofError)

    def test_mark_and_extract(self):
        s = Source("hello world")
        s.inc_n(6)
        s.mark()
        s.inc_n(5)
        assert s.extract() == "world"

    def test_consume(self):
        s = Source("   x")
        s.consume(" ")
        assert s.current == "x"

    def test_consume_min_not_met(self):
        s = Source("x")
        with pytest.raises(UnexpectedCharError):
            s.consume(" ", min=1)

    def test_consume_max(self):
        s = Source("aaab")
        s.consume("a", max=2)
        assert s.idx == 2

    def test_advance_while_until(self):
        s = Source("aaab")
        assert s.advance_while(frozenset("a")) is True
        assert s.current == "b"
        s2 = Source("xyz!")
        s2.advance_until(frozenset("!"))
        assert s2.current == "!"
        assert s2.advance_while(frozenset("!")) is False

    def test_state_restore_on_exception(self):
        s = Source("abc")
        with pytest.raises(RuntimeError), s.state:
            s.inc()
            raise RuntimeError
        assert s.current == "a"

    def test_state_restore_flag(self):
        s = Source("abc")
        with s.state(restore=True):
            s.inc()
        assert s.idx == 0

    def test_linecol(self):
        s = Source("ab\ncd")
        s.inc_n(4)
        assert s._to_linecol() == (2, 1)

    def test_nul_is_not_eof(self):
        s = Source("\0a")
        assert not s.end()
        assert s.inc() is True


class TestExceptions:
    def test_parse_error_attrs(self):
        e = ParseError(3, 7, "boom")
        assert e.line == 3
        assert e.col == 7
        assert "boom" in str(e)
        assert "line 3 col 7" in str(e)

    def test_hierarchy(self):
        assert issubclass(ParseError, ValueError)
        assert issubclass(ParseError, TOMLKitError)
        assert issubclass(NonExistentKey, KeyError)

    def test_messages(self):
        assert "Mixed types" in str(MixedArrayTypesError(1, 1)) or "mixed" in str(
            MixedArrayTypesError(1, 1)
        ).lower()
        assert "Empty key" in str(EmptyKeyError(1, 1))
        # repair R5: messages use double quotes, e.g. 'Key "x" does not exist.'
        # (KeyError subclasses repr() their message, so str() adds outer quotes)
        assert 'Key "x" does not exist.' in str(NonExistentKey("x"))
        assert str(KeyAlreadyPresent("x")) == 'Key "x" already exists.'

    def test_unexpected_char(self):
        e = UnexpectedCharError(1, 2, "@")
        assert "@" in str(e)

    def test_invalid_control_char(self):
        e = InvalidControlChar(1, 1, 1, "strings")
        assert "strings" in str(e)

    def test_invalid_string_error(self):
        e = InvalidStringError("a'b", ["'"], "'")
        assert isinstance(e, ValueError)
