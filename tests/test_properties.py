"""Property-based tests (Hypothesis) for tomlkit.parse and tomlkit.dumps.

Technique: property-based testing, generating many integer inputs
within the TOML 64-bit integer range to check two properties.
"""
from hypothesis import given
from hypothesis import strategies as st

import tomlkit

TOML_INT = st.integers(min_value=-(2**63), max_value=2**63 - 1)


@given(TOML_INT)
def test_parse_reads_back_any_integer(i):
    """Property 1 (parse): the parsed value equals the integer written."""
    doc = tomlkit.parse(f"n = {i}\n")
    assert doc["n"] == i


@given(TOML_INT)
def test_dumps_round_trips_any_integer_document(i):
    """Property 2 (dumps): serializing a parsed document returns the original text."""
    text = f"n = {i}\n"
    assert tomlkit.dumps(tomlkit.parse(text)) == text
