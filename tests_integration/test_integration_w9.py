"""Week 9 integration tests. Each test drives two or more real tomlkit
components (parser, container, items, writer, file I/O) together, no mocks.
Level: integration. RTM ids are given per test."""

import datetime as dt

import pytest

import tomlkit

from tomlkit.toml_file import TOMLFile


# IT1 - RTM R06: dump() -> real file -> load(), text and binary handles
def test_it1_dump_then_load_through_real_text_and_binary_files(tmp_path):
    data = {
        "title": "demo",
        "owner": {"name": "Ada", "ids": [1, 2, 3]},
        "servers": [{"host": "a"}, {"host": "b"}],
    }
    text_path = tmp_path / "t.toml"
    bin_path = tmp_path / "b.toml"
    with open(text_path, "w", encoding="utf-8") as fp:
        tomlkit.dump(data, fp)
    with open(bin_path, "wb") as fp:
        with pytest.raises(TypeError):
            tomlkit.dump(data, fp)  # dump() writes str, so a binary handle is rejected
    bin_path.write_bytes(tomlkit.dumps(data).encode("utf-8"))
    with open(text_path, "r", encoding="utf-8") as fp:
        from_text = tomlkit.load(fp)
    with open(bin_path, "rb") as fp:
        from_bin = tomlkit.load(fp)
    assert from_text.unwrap() == data
    assert from_bin.unwrap() == data


# IT2 - RTM R03/R07/R12: TOMLFile + array/table editing + writer, real filesystem
def test_it2_tomlfile_edit_array_and_table_then_reread(tmp_path):
    path = tmp_path / "cfg.toml"
    path.write_text('# keep me\n[tool]\nnames = ["a", "b"]  # trailing\nlevel = 1\n', encoding="utf-8")
    f = TOMLFile(path)
    doc = f.read()
    doc["tool"]["names"].append("c")
    doc["tool"]["level"] = 2
    doc["tool"]["extra"] = {"k": True}
    f.write(doc)
    saved = path.read_text(encoding="utf-8")
    assert saved.startswith("# keep me\n[tool]\n")
    assert "# trailing" in saved
    expected = {"tool": {"names": ["a", "b", "c"], "level": 2, "extra": {"k": True}}}
    assert tomlkit.parse(saved).unwrap() == expected


# IT3 - RTM R13: out-of-order tables - proxy + container + renderer + parser
def test_it3_out_of_order_tables_edit_add_delete_reserialise():
    src = "[a.b]\nx = 1\n\n[c]\ny = 2\n\n[a.d]\nz = 3\n"
    doc = tomlkit.parse(src)
    doc["a"]["b"]["x"] = 10
    doc["a"]["d"]["w"] = 4
    out = tomlkit.dumps(doc)
    assert tomlkit.parse(out).unwrap() == {
        "a": {"b": {"x": 10}, "d": {"z": 3, "w": 4}},
        "c": {"y": 2},
    }
    del doc["a"]["b"]
    out2 = tomlkit.dumps(doc)
    assert tomlkit.parse(out2).unwrap() == {"a": {"d": {"z": 3, "w": 4}}, "c": {"y": 2}}


# IT4 - RTM R01/R02: builders -> dumps -> parser gives the same data back
def test_it4_built_document_dumps_and_reparses_to_same_data():
    doc = tomlkit.document()
    doc.add(tomlkit.comment("generated"))
    doc.add("title", "demo")
    inline = tomlkit.inline_table()
    inline.append("k", 1)
    server = tomlkit.table()
    server.add("port", 8080)
    server.add("opts", inline)
    server.add("when", tomlkit.date("2026-11-10"))
    doc.add("server", server)
    nodes = tomlkit.aot()
    for host in ("a", "b"):
        t = tomlkit.table()
        t.add("host", host)
        nodes.append(t)
    doc.add("nodes", nodes)
    reparsed = tomlkit.parse(tomlkit.dumps(doc))
    assert reparsed.unwrap() == {
        "title": "demo",
        "server": {"port": 8080, "opts": {"k": 1}, "when": dt.date(2026, 11, 10)},
        "nodes": [{"host": "a"}, {"host": "b"}],
    }


# IT5 - RTM R05: dumps(sort_keys=True) with a nested array of tables, re-parsed
def test_it5_dumps_sort_keys_with_nested_aot_reparses_to_same_data():
    data = {"alpha": 1, "mid": {"y": 2, "x": 1}, "zeta": [{"b": 2, "a": 1}, {"d": 4, "c": 3}]}
    parsed = tomlkit.parse(tomlkit.dumps(data, sort_keys=True))
    assert parsed.unwrap() == data
    # the sort key treats only dicts as tables, so the array of tables sorts with the plain values
    assert list(parsed.keys()) == ["alpha", "zeta", "mid"]
    assert list(parsed["mid"].keys()) == ["x", "y"]
    assert [list(t.keys()) for t in parsed["zeta"]] == [["a", "b"], ["c", "d"]]
    # a plain value must be emitted before any [[table]] header, or TOML would absorb it into that table
    mixed = {"alpha": [{"a": 1}], "zeta": 3}
    reparsed = tomlkit.parse(tomlkit.dumps(mixed, sort_keys=True))
    assert reparsed.unwrap() == mixed
    assert list(reparsed.keys()) == ["zeta", "alpha"]
