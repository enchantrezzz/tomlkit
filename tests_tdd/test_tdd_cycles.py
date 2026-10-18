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
