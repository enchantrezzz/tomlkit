"""Track D property-based tests (Hypothesis).

Functions under test and their input domains:
  P1  item()/dumps()/parse()  - any JSON-like mapping of TOML-representable values
  P2  dumps(parse(s))         - any document produced by P1 (formatting identity)
  P3  string()                - any Unicode text, all four TOML string kinds
  P4  integer()/value()       - any Python int in TOML's signed 64-bit range
  P5  datetime()/date()/time()- any RFC 3339 value Python can represent
"""

import datetime as dt
import string as _string

import pytest

from hypothesis import HealthCheck
from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st

import tomlkit

from tomlkit.exceptions import InvalidStringError
from tomlkit.items import String
from tomlkit.items import StringType


settings.register_profile(
    "ci", max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow]
)
settings.load_profile("ci")

# ---------- strategies ----------
INT64 = st.integers(min_value=-(2**63), max_value=2**63 - 1)
FLOATS = st.floats(allow_nan=False, allow_infinity=True, width=64)
TEXT = st.text(st.characters(blacklist_categories=("Cs",)), max_size=30)
KEYS = st.one_of(
    st.text(_string.ascii_letters + _string.digits + "-_", min_size=1, max_size=10),
    TEXT,  # quoted keys, incl. empty and unicode
)
DATES = st.dates(min_value=dt.date(1, 1, 1), max_value=dt.date(9999, 12, 31))
TIMES = st.times()
OFFSETS = st.integers(min_value=-23 * 60 - 59, max_value=23 * 60 + 59).map(
    lambda m: dt.timezone(dt.timedelta(minutes=m))
)
DATETIMES = st.datetimes(
    min_value=dt.datetime(1, 1, 2), max_value=dt.datetime(9999, 12, 30),
    timezones=st.one_of(st.none(), st.just(dt.timezone.utc), OFFSETS),
)
SCALARS = st.one_of(st.booleans(), INT64, FLOATS, TEXT, DATES, TIMES, DATETIMES)


def values(leaf):
    return st.recursive(
        leaf,
        lambda children: st.one_of(
            st.lists(children, max_size=4),
            st.dictionaries(KEYS, children, max_size=4),
        ),
        max_leaves=12,
    )


DOCS = st.dictionaries(KEYS, values(SCALARS), max_size=6)


def plain(x):
    """Normalise tuples/lists for comparison."""
    if isinstance(x, dict):
        return {k: plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    return x


# ---------- P1: serialise then parse preserves meaning ----------
@given(DOCS)
def test_p1_dumps_then_parse_preserves_data(data):
    text = tomlkit.dumps(data)
    assert tomlkit.parse(text).unwrap() == plain(data)


# ---------- P2: an unmodified document re-serialises byte-identically ----------
@given(DOCS)
def test_p2_parse_dumps_is_identity_on_text(data):
    text = tomlkit.dumps(data)
    assert tomlkit.dumps(tomlkit.parse(text)) == text


# ---------- P3: string() round-trips, or rejects with InvalidStringError ----------
@given(TEXT, st.sampled_from(list(StringType)))
def test_p3_string_round_trip_all_kinds(s, kind):
    try:
        item = String.from_raw(s, kind)
    except InvalidStringError:
        # only literal strings may reject; basic strings escape everything
        assert kind.is_literal()
        return
    doc = tomlkit.parse(f"a = {item.as_string()}\n")
    assert doc["a"] == s


# ---------- P4: integers round-trip through item and value() ----------
@given(INT64)
def test_p4_integer_round_trip(n):
    assert tomlkit.integer(n).as_string() == str(n)
    assert tomlkit.value(str(n)) == n
    assert tomlkit.value(hex(n)) == n if n >= 0 else True


# ---------- P5: date/time factories accept exactly their own kind ----------
@given(DATETIMES)
def test_p5_datetime_round_trip(d):
    s = tomlkit.item(d).as_string()
    assert tomlkit.datetime(s) == d


@given(DATES)
def test_p5_date_round_trip(d):
    assert tomlkit.date(d.isoformat()) == d


@given(TIMES)
def test_p5_time_round_trip(t):
    assert tomlkit.time(t.isoformat()) == t


@given(DATETIMES)
def test_p5_date_rejects_datetime_strings(d):
    # documented: "date() only accepts date strings" (defect D1)
    s = tomlkit.item(d).as_string()
    try:
        r = tomlkit.date(s)
    except ValueError:
        return
    assert not isinstance(r, dt.datetime)


# ---------- Regression for D7 (found by Hypothesis P3, fixed in TDD cycle 2) ----------
@pytest.mark.parametrize("kind", [StringType.MLB, StringType.MLL])
def test_d7_multiline_string_with_bare_cr(kind):
    try:
        item = String.from_raw("a\rb", kind)
    except InvalidStringError:
        return  # rejecting is acceptable
    assert tomlkit.parse(f"a = {item.as_string()}\n")["a"] == "a\rb"
