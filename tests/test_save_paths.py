"""WGS containment and unchanged loose-save discovery, using synthetic folders."""

import base64
import importlib.util
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.editor import EditorApi
from src.save_paths import find_hogwarts_wgs, is_wgs_path, require_loose_save_path


@pytest.fixture
def wgs(tmp_path):
    root = (tmp_path / "Packages" / "WarnerBros.Interactive.PHX_ktmk1xygcecda"
            / "SystemAppData" / "wgs")
    payload = root / "user" / "container" / "ABCDEF"
    payload.parent.mkdir(parents=True)
    payload.write_bytes(b"synthetic payload")
    (payload.parent / "container.1").write_bytes(b"metadata sentinel")
    (payload.parent.parent / "containers.index").write_bytes(b"index sentinel")
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    yield root, payload
    assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == before
    assert not list(root.rglob("Backups"))


@pytest.fixture
def app(monkeypatch):
    # Import the actual App methods without GUI dependencies or constructing Tk.
    monkeypatch.setitem(sys.modules, "customtkinter", SimpleNamespace(
        CTk=object, CTkButton=Mock(return_value=Mock()),
        CTkLabel=Mock(return_value=Mock()), CTkFont=Mock(return_value=Mock())))
    monkeypatch.setitem(sys.modules, "tkinterdnd2", SimpleNamespace(TkinterDnD=SimpleNamespace(Tk=object)))
    spec = importlib.util.spec_from_file_location("src._paths_test_app", Path(__file__).parents[1] / "src/app.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    instance = module.App.__new__(module.App)
    instance.save_directory = None
    instance.backup_dir = None
    instance.current_save_file = None
    instance.selected_button = None
    instance.config = {}
    instance.is_working = False
    instance.path_label = Mock()
    instance._log = Mock()
    instance._refresh_save_list = Mock()
    instance._save_config = Mock()
    instance._update_file_info = Mock()
    instance.save_list_frame = Mock()
    instance.save_list_frame.winfo_children.return_value = []
    monkeypatch.setattr(module.messagebox, "showwarning", Mock())
    return instance, module


def test_wgs_detection_is_title_specific_read_only_and_handles_missing_env(tmp_path, wgs):
    root, payload = wgs
    assert find_hogwarts_wgs(str(tmp_path)) == root
    assert find_hogwarts_wgs("") is None
    assert find_hogwarts_wgs(str(tmp_path / "missing")) is None
    unrelated = tmp_path / "Packages/Other.Game/SystemAppData/wgs"
    unrelated.mkdir(parents=True)
    assert find_hogwarts_wgs(str(tmp_path)) == root
    for path in [root, payload, payload.with_suffix(".sav"), root / "unknown/new.sqlite"]:
        assert is_wgs_path(path)
        with pytest.raises(ValueError, match="Game Pass"):
            require_loose_save_path(path)
    assert not is_wgs_path(tmp_path / "ordinary/HL-00-00.sav")
    assert not is_wgs_path(tmp_path / "wgs-not-a-container/save.sav")


@pytest.mark.parametrize("marker", ["container.index", "containers.index"])
def test_copied_wgs_and_case_insensitive_layout(tmp_path, marker):
    copied = tmp_path / "copied-user"
    copied.mkdir()
    (copied / marker).write_bytes(b"metadata")
    assert is_wgs_path(copied / "container/payload")
    assert is_wgs_path(tmp_path / "SystemAppData/WGS/user/payload")


def test_resolved_directory_alias_is_blocked(tmp_path, wgs):
    root, _ = wgs
    link = tmp_path / "ordinary-looking-folder"
    try:
        link.symlink_to(root, target_is_directory=True)
    except OSError:
        pytest.skip("Creating symbolic links requires Windows Developer Mode or elevated rights")
    assert is_wgs_path(link / "payload.sav")


def test_steam_discovery_uses_newest_save_not_folder_timestamp_and_reports_wgs(app, tmp_path, wgs, monkeypatch):
    instance, _ = app
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    base = tmp_path / "Hogwarts Legacy/Saved/SaveGames"
    for name, folder_timestamp, save_timestamp in [
        ("123", 300, 100),
        ("456", 100, 200),
        ("epic-profile", 400, 150),
    ]:
        directory = base / name
        directory.mkdir(parents=True)
        save = directory / "HL-00-00.sav"
        save.write_bytes(b"synthetic save")
        os.utime(save, (save_timestamp, save_timestamp))
        os.utime(directory, (folder_timestamp, folder_timestamp))
    assert instance._detect_save_directory()
    assert instance.save_directory == (base / "456").resolve()
    assert instance.backup_dir.is_dir()
    instance._refresh_save_list.assert_called_once()
    instance.path_label.configure.assert_called_with(
        text=f"Auto-detected: {(base / '456').resolve()}"
    )
    assert any("newest .sav" in str(call) for call in instance._log.call_args_list)
    assert any("WGS area detected" in str(call) for call in instance._log.call_args_list)


def test_wgs_only_reports_limitation_without_selecting_it(app, tmp_path, wgs, monkeypatch):
    instance, _ = app
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    instance._detect_save_directory()
    assert instance.save_directory is None
    assert instance.backup_dir is None
    instance._refresh_save_list.assert_not_called()
    instance.path_label.configure.assert_called_with(text="WGS unsupported")


def test_config_selection_and_browse_refuse_wgs_before_backup_or_config_write(app, wgs, monkeypatch):
    instance, module = app
    root, payload = wgs
    assert not instance._set_save_directory(payload.parent, "Saved folder")
    monkeypatch.setattr(module.filedialog, "askdirectory", lambda **_: str(root))
    instance._browse_save_directory()
    assert instance.save_directory is None
    assert instance.backup_dir is None
    instance._save_config.assert_not_called()
    assert instance._refresh_save_list.call_count == 2
    module.messagebox.showwarning.assert_called_once()


def test_refused_browse_clears_previous_folder_and_selection(app, tmp_path, wgs):
    instance, module = app
    root, _ = wgs
    instance.save_directory = tmp_path
    instance.current_save_file = tmp_path / "previous.sav"
    instance._refresh_save_list = lambda: module.App._refresh_save_list(instance)
    assert not instance._set_save_directory(root, "Browse")
    assert instance.save_directory is None
    assert instance.current_save_file is None
    assert instance.save_files == []


def test_ordinary_browse_and_refresh_keep_sav_filter(app, tmp_path, monkeypatch):
    instance, module = app
    ordinary = tmp_path / "ordinary"
    ordinary.mkdir()
    for name in ["HL-00-00.sav", "other.sav", "payload", "container.1"]:
        (ordinary / name).write_bytes(b"synthetic")
    monkeypatch.setattr(module.filedialog, "askdirectory", lambda **_: str(ordinary))
    instance._browse_save_directory()
    assert instance.save_directory == ordinary
    assert instance.config["save_directory"] == str(ordinary.resolve())
    assert instance.config["auto_detect_saves"] is False
    instance._save_config.assert_called_once()
    module.App._refresh_save_list(instance)
    assert {p.name for p, _ in instance.save_files} == {"HL-00-00.sav", "other.sav"}


def test_force_auto_detect_switches_back_from_manual_mode_and_persists(app, tmp_path, monkeypatch):
    instance, _ = app
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    base = tmp_path / "Hogwarts Legacy/Saved/SaveGames"
    canonical = base / "123"
    canonical.mkdir(parents=True)
    (canonical / "HL-00-00.sav").write_bytes(b"synthetic save")
    stale = tmp_path / "stale"
    stale.mkdir()
    instance.config = {"save_directory": str(stale), "auto_detect_saves": False}

    instance._auto_detect_save_directory()

    assert instance.save_directory == canonical.resolve()
    assert instance.config["auto_detect_saves"] is True
    assert instance.config["save_directory"] == str(canonical.resolve())
    instance._save_config.assert_called_once()


def test_refresh_and_edit_refuse_wgs_even_if_state_was_set_directly(app, wgs):
    instance, module = app
    root, payload = wgs
    instance.save_directory = payload.parent
    module.App._refresh_save_list(instance)
    assert instance.save_files == []
    instance.current_save_file = payload
    instance._extract_and_edit()
    module.messagebox.showwarning.assert_called_once()


@pytest.mark.parametrize("blocked_target", ["original", "edited", "export"])
def test_editor_api_never_writes_inside_wgs(tmp_path, wgs, monkeypatch, blocked_target):
    root, payload = wgs
    ordinary = tmp_path / "ordinary"
    ordinary.mkdir()
    original = payload if blocked_target == "original" else ordinary / "original.sav"
    decomp = root / "input.decomp" if blocked_target == "edited" else ordinary / "input.decomp"
    status = Mock()
    api = EditorApi(str(decomp), decomp.name, str(original), "hlsaves", str(ordinary), status)
    run = Mock()
    monkeypatch.setattr("src.editor.subprocess.run", run)
    if blocked_target == "export":
        monkeypatch.setitem(sys.modules, "webview", SimpleNamespace(SAVE_DIALOG=30))
        window = Mock()
        window.create_file_dialog.return_value = str(root / "new.sqlite")
        api.set_window(window)
        result = api.export_database(base64.b64encode(b"SQLite format 3\0synthetic").decode(), "sqldb1.sqlite")
        status.assert_not_called()
    else:
        result = api.save_edited_file(base64.b64encode(b"synthetic edited").decode())
        assert not any(call.args[0] == "success" for call in status.call_args_list)
    assert result["success"] is False
    assert "Game Pass" in result["error"]
    run.assert_not_called()
    assert not list(ordinary.iterdir())
