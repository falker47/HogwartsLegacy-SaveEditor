"""Headless desktop API regression tests; no real hlsaves or GUI is started."""

import base64
from contextlib import closing
from pathlib import Path
import sqlite3
import subprocess
import sys
import textwrap
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.editor import EditorApi, get_editor_bridge_js, launch_editor_process
from tests.editor_harness import make_databases, synthetic_save


@pytest.fixture
def session(tmp_path, monkeypatch):
    payloads = make_databases(tmp_path)
    original = tmp_path / "original.sav"
    decompressed = tmp_path / "loaded.dat"
    backup = tmp_path / "Backups" / "original.sav"
    backup.parent.mkdir()
    original.write_bytes(b"original sentinel")
    decompressed.write_bytes(synthetic_save(payloads))
    backup.write_bytes(b"backup sentinel")
    sentinels = {p: p.read_bytes() for p in (original, decompressed, backup)}
    status, window = Mock(), Mock()
    run = Mock(return_value=SimpleNamespace(returncode=0, stderr=""))
    monkeypatch.setattr("src.editor.subprocess.run", run)
    monkeypatch.setitem(sys.modules, "webview", SimpleNamespace(SAVE_DIALOG=30))
    api = EditorApi(str(decompressed), decompressed.name, str(original), "hlsaves", str(tmp_path), status)
    api.set_window(window)
    yield SimpleNamespace(api=api, window=window, status=status, run=run, payloads=payloads,
                          root=tmp_path, sentinels=sentinels)
    for path, content in sentinels.items():
        assert path.read_bytes() == content


def encode(payload):
    return base64.b64encode(payload).decode()


def assert_no_writeback(s):
    s.run.assert_not_called()
    s.status.assert_not_called()
    s.window.destroy.assert_not_called()
    assert not list(s.root.glob("*.edited"))


@pytest.mark.parametrize("selection_type", [str, tuple, list])
def test_export_both_databases_in_same_session(session, selection_type):
    s = session
    for index, payload in enumerate(s.payloads, start=1):
        name = f"sqldb{index}.sqlite"
        target = s.root / name
        s.window.create_file_dialog.return_value = str(target) if selection_type is str else selection_type([str(target)])
        assert s.api.export_database(encode(payload), name) == {"success": True}
        assert target.read_bytes() == payload
        with closing(sqlite3.connect(target)) as db:
            assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert db.execute("SELECT value FROM identity").fetchone() == (f"database-{index}",)
        s.window.create_file_dialog.assert_called_with(
            30, save_filename=name, file_types=("SQLite database (*.sqlite)",)
        )
    assert s.payloads[0] != s.payloads[1]
    assert_no_writeback(s)


@pytest.mark.parametrize("selection", [None, (), [], ""])
def test_cancel_then_export(session, selection):
    s = session
    s.window.create_file_dialog.return_value = selection
    before = set(s.root.rglob("*"))
    assert s.api.export_database(encode(s.payloads[0]), "sqldb1.sqlite") == {"success": False, "cancelled": True}
    assert set(s.root.rglob("*")) == before
    s.window.create_file_dialog.return_value = str(s.root / "next.sqlite")
    assert s.api.export_database(encode(s.payloads[1]), "sqldb2.sqlite")["success"]
    assert_no_writeback(s)


@pytest.mark.parametrize("payload", [None, 12, "%%%", "YQ", "é", "", "YWJj", "U1FMaXRl\n"])
def test_invalid_payload_does_not_open_dialog_or_write(session, payload):
    s = session
    result = s.api.export_database(payload, "sqldb1.sqlite")
    assert result["success"] is False
    assert result["error"]
    s.window.create_file_dialog.assert_not_called()
    assert_no_writeback(s)


@pytest.mark.parametrize("name", ["unknown.sqlite", "hlsave.sav", "../sqldb1.sqlite", None])
def test_unknown_database_name(session, name):
    s = session
    assert not s.api.export_database(encode(s.payloads[0]), name)["success"]
    s.window.create_file_dialog.assert_not_called()
    assert_no_writeback(s)


@pytest.mark.parametrize("destination", ["original.sav", "loaded.dat", "Backups/original.sav", "fixture1.sqlite", "new.sav"])
def test_protected_and_existing_files_are_never_overwritten(session, destination):
    s = session
    target = s.root / destination
    before = target.read_bytes() if target.exists() else None
    s.window.create_file_dialog.return_value = str(target)
    assert not s.api.export_database(encode(s.payloads[1]), "sqldb2.sqlite")["success"]
    assert (target.read_bytes() if target.exists() else None) == before
    assert_no_writeback(s)


def test_hardlink_to_save_is_not_overwritten(session):
    s = session
    target = s.root / "alias.sqlite"
    target.hardlink_to(s.root / "original.sav")
    s.window.create_file_dialog.return_value = str(target)
    assert not s.api.export_database(encode(s.payloads[0]), "sqldb1.sqlite")["success"]
    assert target.read_bytes() == b"original sentinel"
    assert_no_writeback(s)


def test_dialog_and_write_errors_allow_recovery(session, monkeypatch):
    s = session
    s.window.create_file_dialog.side_effect = RuntimeError("dialog failed")
    assert s.api.export_database(encode(s.payloads[0]), "sqldb1.sqlite")["error"] == "dialog failed"
    s.window.create_file_dialog.side_effect = None
    s.window.create_file_dialog.return_value = str(s.root / "missing" / "db.sqlite")
    assert not s.api.export_database(encode(s.payloads[0]), "sqldb1.sqlite")["success"]

    target = s.root / "partial.sqlite"
    s.window.create_file_dialog.return_value = str(target)
    real_open = Path.open

    class FailedWriter:
        def __enter__(self):
            self.file = real_open(target, 'xb')
            return self

        def write(self, data):
            self.file.write(data[:20])
            raise OSError("disk full")

        def __exit__(self, *args):
            self.file.close()

    with monkeypatch.context() as m:
        m.setattr(Path, "open", lambda p, *a, **kw: FailedWriter() if p == target else real_open(p, *a, **kw))
        assert s.api.export_database(encode(s.payloads[0]), "sqldb1.sqlite")["error"] == "disk full"
    assert not target.exists()
    assert s.api.export_database(encode(s.payloads[0]), "sqldb1.sqlite") == {"success": True}
    assert target.read_bytes() == s.payloads[0]
    assert_no_writeback(s)


def test_missing_window_returns_error(session):
    s = session
    s.api.set_window(None)
    assert not s.api.export_database(encode(s.payloads[0]), "sqldb1.sqlite")["success"]
    assert_no_writeback(s)


@pytest.mark.parametrize("outcome", [0, 1, OSError("cannot start"), subprocess.SubprocessError("failed")])
def test_full_save_pipeline_remains_unchanged(session, outcome):
    s = session
    payload = synthetic_save(s.payloads)
    if isinstance(outcome, Exception):
        s.run.side_effect = outcome
    else:
        s.run.return_value = SimpleNamespace(returncode=outcome, stderr="compressor error")
    result = s.api.save_edited_file(encode(payload))
    assert result["success"] is (outcome == 0)
    assert (s.root / "loaded.edited").read_bytes() == payload
    s.run.assert_called_once_with(
        ["hlsaves", "-c", str(s.root / "loaded.edited"), str(s.root / "original.sav")],
        capture_output=True, text=True, cwd=str(s.root)
    )
    assert s.status.call_args.args[0] == ("success" if outcome == 0 else "error")
    s.window.create_file_dialog.assert_not_called()
    s.window.destroy.assert_not_called()
    s.api.close_window()
    s.window.destroy.assert_called_once()


@pytest.mark.parametrize("bridge_source", ["external", "missing", "unreadable"])
def test_launch_uses_executable_bridge_and_sets_window(session, monkeypatch, bridge_source):
    s = session
    app_dir = s.root
    external = get_editor_bridge_js(str(Path(__file__).resolve().parents[1]))
    if bridge_source != "missing":
        (app_dir / "assets").mkdir()
        (app_dir / "assets" / "editor_bridge.js").write_text(external, encoding="utf-8")
    if bridge_source == "unreadable":
        monkeypatch.setattr(Path, "read_text", Mock(side_effect=OSError("unreadable")))
    window = Mock()
    webview = SimpleNamespace(create_window=Mock(return_value=window), start=lambda on_loaded: on_loaded())
    monkeypatch.setitem(sys.modules, "webview", webview)
    status = app_dir / "status.txt"
    launch_editor_process(str(app_dir / "editor.html"), str(app_dir / "loaded.dat"), "loaded.dat",
                          str(app_dir / "original.sav"), "hlsaves", str(app_dir), str(status), 1920, 1080)
    # Parity check complements Node execution of both actual loader paths.
    js = window.evaluate_js.call_args.args[0]
    assert textwrap.dedent(js).strip() == external.strip()
    api = webview.create_window.call_args.kwargs["js_api"]
    assert api._window is window
    assert base64.b64decode(api.get_file_data()) == (app_dir / "loaded.dat").read_bytes()
    assert api.get_file_name() == "loaded.dat"
    assert status.read_bytes() == b"editing|Editor opened"
