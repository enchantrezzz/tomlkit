"""Tests written first (red) for the Week 8+ TDD log. One section per cycle."""

import datetime as dt

import pytest

import tomlkit


# ---- Cycle 1 (D1): date() must reject strings that are not plain dates ----
@pytest.mark.parametrize(
    "raw", ["1979-05-27T07:32:00", "1979-05-27 07:32:00Z", "0001-10-30 00:00", "1979-05-27T07:32:00-08:00"]
)
def test_c1_date_rejects_datetime_strings(raw):
    with pytest.raises(ValueError, match=r"date\(\) only accepts date strings"):
        tomlkit.date(raw)


def test_c1_date_still_accepts_plain_dates():
    d = tomlkit.date("1979-05-27")
    assert type(d.unwrap()) is dt.date
    assert d.as_string() == "1979-05-27"


# ---- Cycle 2 (D7): multiline strings must not emit a bare CR ----
from tomlkit.exceptions import InvalidStringError  # noqa: E402
from tomlkit.items import String, StringType  # noqa: E402


@pytest.mark.parametrize("value", ["a\rb", "\r", "a\r\rb", "end\r"])
def test_c2_multiline_basic_escapes_bare_cr(value):
    s = String.from_raw(value, StringType.MLB)
    assert "\r" not in s.as_string().replace("\r\n", "")
    assert tomlkit.parse(f"x = {s.as_string()}\n")["x"] == value


def test_c2_multiline_basic_keeps_crlf_line_breaks():
    s = String.from_raw("a\r\nb", StringType.MLB)
    assert s.as_string() == '"""a\r\nb"""'


@pytest.mark.parametrize("value", ["a\rb", "\r"])
def test_c2_multiline_literal_rejects_bare_cr(value):
    with pytest.raises(InvalidStringError):
        String.from_raw(value, StringType.MLL)


def test_c2_multiline_literal_allows_crlf():
    assert String.from_raw("a\r\nb", StringType.MLL).as_string() == "'''a\r\nb'''"


# ---- Cycle 3 (D6): comment() must always produce valid TOML ----
@pytest.mark.parametrize(
    "text,expected",
    [("a\rb", "# a\n# b"), ("a\r\rb", "# a\n#\n# b"), ("a\r\nb", "# a\r\n# b"), ("a\nb", "# a\n# b")],
)
def test_c3_comment_splits_every_line_break(text, expected):
    doc = tomlkit.document()
    doc.add(tomlkit.comment(text))
    doc.add("k", 1)
    out = doc.as_string()
    assert out.startswith(expected)
    assert tomlkit.parse(out)["k"] == 1
