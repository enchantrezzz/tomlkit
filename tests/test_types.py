"""Tests for tomlkit/_types.py, targeting mutants 6, 7, 9 and 10 from the Week 10 mutation run.

Techniques: normal-case functional testing (mutants 6, 7, 9) and
decision coverage on the `if result is NotImplemented` branch (mutant 10).
"""
import pytest

from tomlkit._types import _CustomDict
from tomlkit._types import _CustomList
from tomlkit._types import wrap_method


def test_list_add_returns_combined_list():
    """Mutant 6 (line 54). Technique: normal-case functional testing."""
    result = _CustomList([1, 2]) + [3]
    assert result == [1, 2, 3]


@pytest.mark.xfail(
    strict=True,
    reason="DEFECT found by mutation testing: _CustomDict.__or__ starts from "
           "copy(), which returns {}, so existing keys are dropped.",
)
def test_dict_or_returns_merged_dict():
    """Mutant 7 (line 66). Technique: normal-case functional testing."""
    result = _CustomDict({"a": 1}) | {"b": 2}
    assert result == {"a": 1, "b": 2}


class _Wrapped:
    def __init__(self, value):
        self.value = value

    def _new(self, value):
        return _Wrapped(value)

    @wrap_method
    def add(self, other):
        return self.value + other

    @wrap_method
    def passthrough(self, other):
        return NotImplemented


def test_wrap_method_rewraps_result():
    """Mutant 9 (line 85). Technique: normal-case functional testing."""
    result = _Wrapped(2).add(3)
    assert isinstance(result, _Wrapped)
    assert result.value == 5


def test_wrap_method_preserves_not_implemented():
    """Mutant 10 (line 86). Technique: decision coverage on `if result is NotImplemented`."""
    assert _Wrapped(2).passthrough(3) is NotImplemented


import pytest as _pytest
from tomlkit import key as _key
from tomlkit import parse as _parse


@_pytest.mark.xfail(strict=True, reason="DEFECT D5: key([]) serialises to an empty, unparseable key")
def test_empty_key_list_serialises_to_parseable_key():
    """R15 (D5). Technique: boundary value analysis on the empty list."""
    _parse(_key([]).as_string() + " = 1")
