"""Step definitions for features/edit_config.feature (pytest-bdd)."""

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tomlkit.toml_file import TOMLFile

scenarios("features/edit_config.feature")


def _get(doc, dotted):
    node = doc
    for part in dotted.split("."):
        node = node[part]
    return node


def _set(doc, dotted, value):
    *parents, last = dotted.split(".")
    node = doc
    for part in parents:
        node = node[part]
    node[last] = value


@pytest.fixture
def ctx():
    return {}


@given("a config file containing:", target_fixture="path")
def config_file(tmp_path, docstring):
    p = tmp_path / "pyproject.toml"
    p.write_bytes((docstring + "\n").encode())
    return p


@when(parsers.parse('I open the file with tomlkit and set "{key}" to "{value}"'))
def open_and_set(path, ctx, key, value):
    ctx["file"] = TOMLFile(path)
    ctx["doc"] = ctx["file"].read()
    _set(ctx["doc"], key, value)


@when("I save the file")
def save(ctx):
    ctx["file"].write(ctx["doc"])


@then("the file on disk is exactly:")
def file_is_exactly(path, docstring):
    assert path.read_bytes().decode() == docstring + "\n"


@then(parsers.parse('reading "{key}" from the saved file gives "{value}"'))
def read_back(path, key, value):
    assert _get(TOMLFile(path).read(), key) == value
