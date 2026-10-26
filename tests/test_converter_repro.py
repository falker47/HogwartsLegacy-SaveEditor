"""Validate the public reproduction fixture and its no-overwrite/runtime guards."""
import importlib.util
from io import BytesIO
from pathlib import Path
import sqlite3
import hashlib

import pytest

from src.save_metadata import Reader

spec = importlib.util.spec_from_file_location("converter_repro", Path(__file__).parents[1] / "scripts/reproduce_converter_realloc.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_fixture_contains_two_valid_independent_synthetic_databases():
    payload = probe.fixture_bytes()
    stream = BytesIO(payload)
    reader = Reader(stream, len(payload))
    assert reader.read(4) == b"GVAS" and reader.number("i") == 2
    reader.number("i")
    reader.read(10)
    assert reader.string() == "synthetic"
    assert reader.number("i") == 3 and reader.number("i") == 0
    assert reader.string().endswith(".PersistentGameData")
    images = []
    for name, kind, subtype, value in reader.tags():
        assert name in ("RawDatabaseImage", "RawExclusiveImage")
        assert kind == "ArrayProperty" and subtype == "ByteProperty"
        image = value.read(value.number("i"))
        with sqlite3.connect(":memory:") as db:
            db.deserialize(image)
            assert db.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
            images.append(db.execute("SELECT length(value) FROM synthetic").fetchone()[0])
    assert images == [36000, 100]
    assert payload == probe.fixture_bytes()


def test_hash_mismatch_does_not_create_output_or_execute_native_code(tmp_path):
    fake_converter = tmp_path / "not-a-program"
    fake_converter.write_bytes(b"not executable")
    target = tmp_path / "new-output"
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        probe.reproduce(fake_converter, target, probe.PINNED_SHA256)
    assert not target.exists()


def test_existing_output_directory_is_never_reused(tmp_path):
    fake_converter = tmp_path / "not-a-program"
    fake_converter.write_bytes(b"not executable")
    target = tmp_path / "existing-output"
    target.mkdir()
    sentinel = target / "keep.txt"
    sentinel.write_text("keep")
    with pytest.raises(FileExistsError):
        probe.reproduce(fake_converter, target, hashlib.sha256(fake_converter.read_bytes()).hexdigest())
    assert list(target.iterdir()) == [sentinel] and sentinel.read_text() == "keep"


@pytest.mark.parametrize("stages,exact,source,expected", [
    ([{"exit_code": 0}, {"exit_code": 0}], True, True, 0),
    ([{"exit_code": 0}, {"exit_code": 1}], True, True, 1),
    ([{"exit_code": 0}, {"exit_code": 0}], True, False, 1),
    ([{"exit_code": 0}, {"exit_code": 0}], False, True, 1),
    ([{"exit_code": 0}], True, True, 1),
])
def test_cli_requires_both_successful_stages_and_preserved_source(
        monkeypatch, capsys, stages, exact, source, expected):
    monkeypatch.setattr("sys.argv", ["probe", "--converter", "unused", "--out-dir", "unused"])
    monkeypatch.setattr(probe, "reproduce", lambda *args: {
        "stages": stages, "exact_roundtrip": exact, "source_unchanged": source})
    assert probe.main() == expected
    assert capsys.readouterr().out
