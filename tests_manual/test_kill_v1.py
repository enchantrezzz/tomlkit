"""Manual tests written to kill mutants that survived the AI-only suite (mutmut v1).

Each test names the mutant it targets, the test-design technique that justifies it
(EP = equivalence partitioning, BVA = boundary value analysis, DT = decision table),
and the requirement in the RTM it strengthens.
"""

import datetime as dt

import pytest

import tomlkit
from tomlkit._utils import parse_rfc3339
from tomlkit.exceptions import InvalidCharInStringError, InvalidNumberError
from tomlkit.source import Source
from tomlkit.toml_file import TOMLFile


# K1 - exceptions.InvalidNumberError.__init__ mutmut_3  ("Invalid number" -> "invalid number")
# Technique: EP on error outputs - the user-visible message is part of the contract.  RTM: R04
def test_k1_invalid_number_message_and_position_exact():
    with pytest.raises(InvalidNumberError) as exc:
        tomlkit.parse("a = 01")
    assert str(exc.value) == "Invalid number at line 1 col 6"
    assert (exc.value.line, exc.value.col) == (1, 6)


# K2 - source.Source._to_linecol mutmut_7  (">" -> ">=")
# Technique: BVA - the index exactly on a newline vs. the first char of the next line.  RTM: R04
@pytest.mark.parametrize("advance,expected", [(2, (1, 2)), (3, (2, 0))])
def test_k2_line_col_at_line_boundary(advance, expected):
    s = Source("ab\ncd")
    s.inc_n(advance)
    assert s._to_linecol() == expected


# K3 - parser._parse_escaped_char mutmut_1  ("multiline and ws" -> "multiline or ws")
# Technique: EP - "backslash + whitespace" is valid only in multiline strings; the AI only
# tested an invalid letter escape (\q).  RTM: R01, R04
def test_k3_backslash_space_rejected_in_single_line_string():
    with pytest.raises(InvalidCharInStringError) as exc:
        tomlkit.parse('a = "x\\ y"')
    assert (exc.value.line, exc.value.col) == (1, 7)


def test_k3_backslash_newline_is_line_continuation_in_multiline():
    assert tomlkit.parse('a = """x\\\n   y"""')["a"] == "xy"


# K4 - _utils.parse_rfc3339 mutmut_66  (tz[1:] -> tz[2:])
# Technique: BVA - two-digit offset hours (>= 10). AI tests used +05:30 / -08:00 only,
# where dropping the leading "0" happens to give the same number.  RTM: R08
@pytest.mark.parametrize(
    "tz,offset",
    [("+10:00", dt.timedelta(hours=10)), ("-11:30", -dt.timedelta(hours=11, minutes=30)),
     ("+23:59", dt.timedelta(hours=23, minutes=59))],
)
def test_k4_two_digit_utc_offsets(tz, offset):
    assert parse_rfc3339(f"1979-05-27T07:32:00{tz}").utcoffset() == offset


# K5 - _utils.parse_rfc3339 mutmut_163  ([:6] -> [:7] in the time-only branch)
# Technique: EP - the same "truncate to microseconds" rule exists in two branches;
# the AI tested it only for datetimes.  RTM: R08
def test_k5_time_fraction_truncated_to_microseconds():
    assert parse_rfc3339("07:32:00.1234567") == dt.time(7, 32, 0, 123456)
    assert tomlkit.parse("a = 07:32:00.9999999")["a"] == dt.time(7, 32, 0, 999999)


# K6 - items.Array.insert mutmut_14  ("pos < 0" -> "pos <= 0")
# Technique: BVA - index 0 is the boundary between the negative and positive partitions;
# the AI inserted at 1 and -1 only.  RTM: R12
def test_k6_insert_at_index_zero():
    a = tomlkit.array("[1, 2]")
    a.insert(0, 0)
    assert a == [0, 1, 2]
    assert tomlkit.parse(f"x = {a.as_string()}")["x"] == [0, 1, 2]
    a.append(3)
    assert tomlkit.parse(f"x = {a.as_string()}")["x"] == [0, 1, 2, 3]


@pytest.mark.xfail(strict=True, reason="DEFECT D8: insert at 0 renders '[0,1, 2]' (space lost)")
def test_k6_insert_at_index_zero_keeps_spacing():
    a = tomlkit.array("[1, 2]")
    a.insert(0, 0)
    assert a.as_string() == "[0, 1, 2]"


# K7 - items.Array.__delitem__ mutmut_13  (slice step argument dropped)
# Technique: EP - stepped slices are a separate partition from contiguous slices.  RTM: R12
@pytest.mark.parametrize("sl,expected", [(slice(None, None, 2), [2, 4]), (slice(1, None, 2), [1, 3, 5])])
def test_k7_delete_stepped_slice(sl, expected):
    a = tomlkit.array("[1, 2, 3, 4, 5]")
    del a[sl]
    assert a == expected
    assert tomlkit.parse(f"x = {a.as_string()}")["x"] == expected


# K8 - items.Array.add_line mutmut_8  ("\r" check disabled)
# Technique: EP - TOML has two line-break characters; the AI tested only "\n".  RTM: R14
@pytest.mark.parametrize("bad", ["a\nb", "a\rb", "a\r\nb"])
def test_k8_add_line_comment_rejects_any_line_break(bad):
    a = tomlkit.array()
    with pytest.raises(ValueError, match="line breaks"):
        a.add_line(1, comment=bad)
    assert a == []


# K9 - items.item mutmut_76  (AoT tables sorted by value instead of key)
# Technique: DT - sort_keys x {table, array of tables}; the AI covered only the table row.  RTM: R05
def test_k9_sort_keys_inside_array_of_tables():
    out = tomlkit.dumps({"t": [{"b": 1, "a": 2}, {"d": 0, "c": 9}]}, sort_keys=True)
    assert out == "[[t]]\na = 2\nb = 1\n\n[[t]]\nc = 9\nd = 0\n"


# K10 - container.Container._replace_at mutmut_3  (idx[1:] -> idx[2:])
# Technique: BVA on fragment count - a key split across 3 out-of-order fragments
# (the AI's out-of-order tests used 2).  RTM: R13
def test_k10_replace_table_split_across_three_fragments():
    src = "[a.x]\nv = 1\n\n[b]\nw = 2\n\n[a.y]\nv = 2\n\n[c]\nu = 3\n\n[a.z]\nv = 3\n"
    doc = tomlkit.parse(src)
    doc["a"] = 5
    out = doc.as_string()
    assert out == "a = 5\n[b]\nw = 2\n\n[c]\nu = 3\n\n"
    assert tomlkit.parse(out).unwrap() == {"a": 5, "b": {"w": 2}, "c": {"u": 3}}


# K11 - toml_file.TOMLFile.write mutmut_10  (LF normalisation replaced)
# Technique: EP - writing a document whose line endings differ from the file's.
# The AI only wrote back the same document it had read.  RTM: R07
def test_k11_write_normalises_foreign_crlf_to_files_lf(tmp_path):
    p = tmp_path / "c.toml"
    p.write_bytes(b"a = 1\n")
    f = TOMLFile(p)
    f.read()  # detects LF
    f.write(tomlkit.parse("b = 2\r\nc = 3\r\n"))
    assert p.read_bytes() == b"b = 2\nc = 3\n"
