"""AI-generated (prompt P6): TOMLFile read/write."""

import pytest

from tomlkit.toml_file import TOMLFile


@pytest.fixture
def make(tmp_path):
    def _make(content: bytes):
        p = tmp_path / "c.toml"
        p.write_bytes(content)
        return p

    return _make


class TestTOMLFile:
    def test_read_values(self, make):
        p = make(b'a = 1\n[t]\nb = "x"\n')
        doc = TOMLFile(p).read()
        assert doc["a"] == 1
        assert doc["t"]["b"] == "x"

    def test_accepts_str_path(self, make):
        p = make(b"a = 1\n")
        assert TOMLFile(str(p)).read()["a"] == 1

    def test_round_trip_lf(self, make):
        data = b"# c\na = 1\n"
        p = make(data)
        f = TOMLFile(p)
        f.write(f.read())
        assert p.read_bytes() == data

    def test_round_trip_crlf(self, make):
        data = b"# c\r\na = 1\r\nb = 2\r\n"
        p = make(data)
        f = TOMLFile(p)
        doc = f.read()
        doc["c"] = 3
        f.write(doc)
        out = p.read_bytes()
        assert b"c = 3\r\n" in out
        assert b"\n" not in out.replace(b"\r\n", b"")

    def test_round_trip_mixed_kept(self, make):
        data = b"a = 1\r\nb = 2\n"
        p = make(data)
        f = TOMLFile(p)
        f.write(f.read())
        assert p.read_bytes() == data

    def test_edit_and_write(self, make):
        p = make(b"a = 1 # keep\n")
        f = TOMLFile(p)
        doc = f.read()
        doc["a"] = 2
        f.write(doc)
        assert p.read_text() == "a = 2 # keep\n"

    def test_utf8(self, make):
        p = make('name = "café"\n'.encode())
        assert TOMLFile(p).read()["name"] == "café"

    def test_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            TOMLFile(tmp_path / "nope.toml").read()

    def test_write_new_file(self, tmp_path):
        import tomlkit

        p = tmp_path / "new.toml"
        f = TOMLFile(p)
        f.write(tomlkit.parse("a = 1\n"))
        assert p.exists()
        assert "a = 1" in p.read_text()
