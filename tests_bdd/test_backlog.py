"""Step definitions for features/backlog.feature (pytest-bdd)."""

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tomlkit.exceptions import ParseError
from tomlkit.toml_file import TOMLFile

scenarios("features/backlog.feature")


@pytest.fixture
def ctx():
    return {}


# --- Scenario 1: a typo is reported at the right place (R04) ---


@given(parsers.parse('a config file whose third line is "{line}"'), target_fixture="path")
def file_with_bad_third_line(tmp_path, ctx, line):
    p = tmp_path / "pyproject.toml"
    p.write_bytes(f"# Project settings\n[project]\n{line}\n".encode())
    ctx["original"] = p.read_bytes()
    return p


@when("I try to open it with tomlkit")
def try_open(path, ctx):
    try:
        TOMLFile(path).read()
    except ParseError as exc:
        ctx["error"] = exc


@then(parsers.parse("I get a parse error that names line {n:d}"))
def error_names_line(ctx, n):
    assert "error" in ctx, "tomlkit accepted the file without a parse error"
    assert ctx["error"].line == n


@then("the file on disk is unchanged")
def file_unchanged(path, ctx):
    assert path.read_bytes() == ctx["original"]


# --- Scenario 2: editing a Windows file keeps CRLF (R07) ---


@given("a config file saved with CRLF line endings", target_fixture="path")
def crlf_file(tmp_path):
    p = tmp_path / "pyproject.toml"
    p.write_bytes(b'[project]\r\nname = "demo"\r\n\r\n[tool.ruff]\r\ntarget-version = "py39"\r\n')
    return p


@when(parsers.parse('I add the key "{key}" with value {value:d} and save'))
def add_key_and_save(path, key, value):
    f = TOMLFile(path)
    doc = f.read()
    *parents, last = key.split(".")
    node = doc
    for part in parents:
        node = node[part]
    node[last] = value
    f.write(doc)


@then("every line in the file ends with CRLF")
def all_crlf(path):
    data = path.read_bytes()
    assert data.count(b"\n") == data.count(b"\r\n") > 0
    assert data.count(b"\r") == data.count(b"\r\n")


@then(parsers.parse("the new key reads back as {value:d}"))
def new_key_reads_back(path, value):
    assert TOMLFile(path).read()["tool"]["ruff"]["line-length"] == value
