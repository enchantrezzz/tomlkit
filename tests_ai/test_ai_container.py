"""AI-generated (prompt P4): document editing via Container / TOMLDocument."""

import copy

import pytest

import tomlkit
from tomlkit.exceptions import KeyAlreadyPresent, NonExistentKey


CONFIG = """\
# Project config
[tool]
name = "demo"  # the name

# deps follow
[tool.deps]
requests = "^2.0"
"""


class TestReadAccess:
    def test_getitem_and_get(self):
        doc = tomlkit.parse(CONFIG)
        assert doc["tool"]["name"] == "demo"
        assert doc.get("missing") is None
        assert doc.get("missing", 5) == 5

    def test_missing_key_raises_nonexistent(self):
        doc = tomlkit.parse(CONFIG)
        with pytest.raises(NonExistentKey):
            doc["nope"]

    def test_nonexistent_is_keyerror(self):
        doc = tomlkit.parse(CONFIG)
        with pytest.raises(KeyError):
            doc["nope"]

    def test_contains_keys_items(self):
        doc = tomlkit.parse("a = 1\nb = 2\n")
        assert "a" in doc
        assert list(doc.keys()) == ["a", "b"]
        assert list(doc.values()) == [1, 2]
        assert dict(doc.items()) == {"a": 1, "b": 2}
        assert len(doc) == 2

    def test_item_method(self):
        doc = tomlkit.parse("a = 1\n")
        assert doc.item("a") == 1
        with pytest.raises(NonExistentKey):
            doc.item("b")

    def test_last_item(self):
        doc = tomlkit.parse("a = 1\nb = 2\n")
        assert doc.last_item() == 2


class TestEditingPreservesStyle:
    def test_update_value_keeps_comment(self):
        doc = tomlkit.parse(CONFIG)
        doc["tool"]["name"] = "renamed"
        assert doc.as_string() == CONFIG.replace('"demo"', '"renamed"')

    def test_add_key_to_existing_table(self):
        doc = tomlkit.parse(CONFIG)
        doc["tool"]["deps"]["click"] = "^8"
        out = doc.as_string()
        assert out.startswith("# Project config\n")
        assert 'click = "^8"' in out
        assert tomlkit.parse(out)["tool"]["deps"]["click"] == "^8"

    def test_add_new_top_level_table(self):
        doc = tomlkit.parse(CONFIG)
        doc["extra"] = {"k": 1}
        out = doc.as_string()
        assert out.startswith(CONFIG)
        assert out.endswith("[extra]\nk = 1\n")

    def test_add_scalar_goes_before_tables(self):
        doc = tomlkit.parse("[t]\nx = 1\n")
        doc["top"] = 1
        assert tomlkit.parse(doc.as_string())["top"] == 1
        assert doc.as_string().index("top = 1") < doc.as_string().index("[t]")

    def test_delete_key_removes_line(self):
        doc = tomlkit.parse("a = 1\nb = 2\nc = 3\n")
        del doc["b"]
        assert doc.as_string() == "a = 1\nc = 3\n"

    def test_delete_table(self):
        doc = tomlkit.parse(CONFIG)
        del doc["tool"]["deps"]
        assert "requests" not in doc.as_string()
        assert "deps" not in doc["tool"]

    def test_replace_table_with_scalar(self):
        doc = tomlkit.parse("[a]\nx = 1\n")
        doc["a"] = 5
        assert doc.unwrap() == {"a": 5}

    def test_replace_preserves_position(self):
        doc = tomlkit.parse("a = 1\nb = 2\nc = 3\n")
        doc["b"] = "two"
        assert doc.as_string() == 'a = 1\nb = "two"\nc = 3\n'

    def test_rename_by_pop_and_set(self):
        doc = tomlkit.parse("a = 1\n")
        doc["z"] = doc.pop("a")
        assert doc.unwrap() == {"z": 1}

    def test_update(self):
        doc = tomlkit.parse("a = 1\n")
        doc.update({"a": 2, "b": 3})
        assert doc.unwrap() == {"a": 2, "b": 3}


class TestAddAndAppend:
    def test_add_duplicate_raises(self):
        doc = tomlkit.document()
        doc.add("a", 1)
        with pytest.raises(KeyAlreadyPresent):
            doc.add("a", 2)

    def test_append_duplicate_raises(self):
        doc = tomlkit.parse("a = 1\n")
        with pytest.raises(KeyAlreadyPresent):
            doc.append("a", 2)

    def test_add_comment_and_newline(self):
        doc = tomlkit.document()
        doc.add(tomlkit.comment("header"))
        doc.add(tomlkit.nl())
        doc.add("a", 1)
        assert doc.as_string() == "# header\n\na = 1\n"

    def test_remove_missing_raises(self):
        doc = tomlkit.document()
        with pytest.raises(NonExistentKey):
            doc.remove("x")

    def test_add_multiple_tables_order(self):
        doc = tomlkit.document()
        doc["a"] = {"x": 1}
        doc["b"] = {"y": 2}
        assert doc.as_string() == "[a]\nx = 1\n\n[b]\ny = 2\n"


class TestDottedAndOutOfOrder:
    def test_dotted_keys_access(self):
        doc = tomlkit.parse("a.b = 1\na.c = 2\n")
        assert doc["a"] == {"b": 1, "c": 2}

    def test_dotted_key_edit(self):
        doc = tomlkit.parse("a.b = 1\na.c = 2\n")
        doc["a"]["b"] = 10
        assert doc.as_string() == "a.b = 10\na.c = 2\n"

    def test_dotted_key_add(self):
        doc = tomlkit.parse("a.b = 1\n")
        doc["a"]["c"] = 2
        assert tomlkit.parse(doc.as_string()).unwrap() == {"a": {"b": 1, "c": 2}}

    def test_out_of_order_table_proxy(self):
        src = "[a.x]\nv = 1\n\n[b]\nw = 2\n\n[a.y]\nv = 3\n"
        doc = tomlkit.parse(src)
        a = doc["a"]
        assert set(a.keys()) == {"x", "y"}
        assert a["y"]["v"] == 3

    def test_out_of_order_edit(self):
        src = "[a.x]\nv = 1\n\n[b]\nw = 2\n\n[a.y]\nv = 3\n"
        doc = tomlkit.parse(src)
        doc["a"]["y"]["v"] = 30
        assert doc.as_string() == src.replace("v = 3", "v = 30")

    def test_out_of_order_add_key(self):
        src = "[a.x]\nv = 1\n\n[b]\nw = 2\n\n[a.y]\nv = 3\n"
        doc = tomlkit.parse(src)
        doc["a"]["z"] = 1
        assert tomlkit.parse(doc.as_string())["a"]["z"] == 1

    def test_out_of_order_delete(self):
        src = "[a.x]\nv = 1\n\n[b]\nw = 2\n\n[a.y]\nv = 3\n"
        doc = tomlkit.parse(src)
        del doc["a"]["x"]
        assert "a.x" not in doc.as_string()
        assert doc.unwrap() == {"a": {"y": {"v": 3}}, "b": {"w": 2}}


class TestUnwrapCopySetdefault:
    def test_unwrap_plain_types(self):
        doc = tomlkit.parse(CONFIG)
        u = doc.unwrap()
        assert u == {"tool": {"name": "demo", "deps": {"requests": "^2.0"}}}
        assert type(u) is dict
        assert type(u["tool"]["name"]) is str

    def test_value_property(self):
        doc = tomlkit.parse("a = 1\n")
        assert doc.value == {"a": 1}

    def test_copy_is_shallow_independent_top_level(self):
        doc = tomlkit.parse("a = 1\n")
        c = doc.copy()
        c["b"] = 2
        assert "b" not in doc

    def test_deepcopy(self):
        doc = tomlkit.parse(CONFIG)
        c = copy.deepcopy(doc)
        c["tool"]["name"] = "x"
        assert doc["tool"]["name"] == "demo"
        assert c.as_string() != doc.as_string()

    def test_setdefault_existing(self):
        doc = tomlkit.parse("a = 1\n")
        assert doc.setdefault("a", 2) == 1

    def test_setdefault_new(self):
        doc = tomlkit.parse("a = 1\n")
        assert doc.setdefault("b", 2) == 2
        assert doc["b"] == 2

    def test_clear(self):
        doc = tomlkit.parse("a = 1\n")
        doc.clear()
        assert len(doc) == 0


class TestEquality:
    def test_doc_equals_dict(self):
        assert tomlkit.parse("a = 1\n[t]\nb = 2\n") == {"a": 1, "t": {"b": 2}}

    def test_str_and_repr(self):
        doc = tomlkit.parse("a = 1\n")
        assert "a" in repr(doc)
        assert str(doc) == str({"a": 1})
