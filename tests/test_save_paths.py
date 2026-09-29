"""WGS containment and unchanged loose-save discovery, using synthetic folders."""

import base64
from concurrent.futures import Future
import importlib.util
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.editor import EditorApi
from src.save_paths import find_hogwarts_wgs, is_wgs_path, require_loose_save_path
from src.save_browser import SaveBrowser
from tests.test_save_browser import character, player


class ImmediateExecutor:
    def submit(self, fn, *args):
        future = Future()
        future.set_result(fn(*args))
        return future


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
        CTk=object, CTkButton=Mock(return_value=Mock()), CTkFrame=Mock(side_effect=lambda *a, **k: Mock()),
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
    instance.save_browser = SaveBrowser()
    instance._browser_executor = ImmediateExecutor()
    instance._browser_future = None
    instance._browser_generation = 0
    instance._browser_directory = None
    instance._browser_poll_id = None
    instance._save_entries = {}
    instance.save_files = []
    instance.profile_menu = Mock()
    instance.selected_profile = None
    instance.location_locale = 'en'
    instance.catalog_label = Mock()
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
    assert instance.backup_dir == (base / '456' / 'Backups').resolve()
    assert not instance.backup_dir.exists()  # listing must be read-only
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
    for name in ["HL-00-00.sav", "other.sav", "payload", "container.1", "SaveGameList.sav", "SavedUserOptions.sav"]:
        (ordinary / name).write_bytes(b"synthetic")
    (ordinary / 'renamed.sav').write_bytes(player())
    monkeypatch.setattr(module.filedialog, "askdirectory", lambda **_: str(ordinary))
    instance._browse_save_directory()
    assert instance.save_directory == ordinary
    assert instance.config["save_directory"] == str(ordinary.resolve())
    assert instance.config["auto_detect_saves"] is False
    instance._save_config.assert_called_once()
    module.App._refresh_save_list(instance)
    assert {e.filename for e in instance.save_files} == {"HL-00-00.sav", "renamed.sav"}


def test_card_selection_uses_original_path_and_refresh_retains_it(app, tmp_path):
    instance, module = app
    original = tmp_path / 'renamed.sav'
    original.write_bytes(player(stem='HL-02-10', kind='AUTO'))
    instance.save_directory = tmp_path
    module.App._refresh_save_list(instance)
    card = instance._create_save_card(instance.save_files[0])
    handler = next(call.args[1] for call in card.bind.call_args_list if call.args[0] == '<Button-1>')
    handler(None)
    assert instance.current_save_file == original
    module.App._refresh_save_list(instance)
    assert instance.current_save_file == original


def test_profile_filter_has_latest_profile_default_and_all_option(app, tmp_path):
    instance, module = app
    for name in ['HL-02-04.sav', 'HL-03-04.sav']:
        (tmp_path / name).write_bytes(player())
    instance.save_directory = tmp_path
    module.App._refresh_save_list(instance)
    assert instance.selected_profile == 'Profile 2'
    instance._on_profile_changed('Profile 3')
    assert [e.filename for e in instance.visible_save_files] == ['HL-03-04.sav']
    instance._on_profile_changed('All profiles')
    assert len(instance.visible_save_files) == 2


def test_named_profiles_keep_ids_selection_and_paths_across_name_changes(app, tmp_path):
    instance, module = app
    for profile in (2, 3):
        (tmp_path / f'HL-0{profile}-04.sav').write_bytes(player(
            profile=profile, character_info=character('Same Example', profile=profile)))
    instance.save_directory = tmp_path
    module.App._refresh_save_list(instance)
    instance.profile_menu.configure.assert_called_with(values=[
        'All profiles', 'Profile 2 — Same Example', 'Profile 3 — Same Example'])
    instance._on_profile_changed('Profile 3 — Same Example')
    selected = tmp_path / 'HL-03-04.sav'
    instance.current_save_file = selected
    selected.write_bytes(player(profile=3, character_info=character('New Example', profile=3)))
    module.App._refresh_save_list(instance)
    assert instance.selected_profile == 'Profile 3'
    instance.profile_menu.set.assert_called_with('Profile 3 — New Example')
    assert [e.path for e in instance.visible_save_files] == [selected]
    assert instance.current_save_file == selected
    selected.write_bytes(player(profile=3))
    module.App._refresh_save_list(instance)
    instance.profile_menu.set.assert_called_with('Profile 3')
    assert instance.current_save_file == selected
    instance._on_profile_changed('All profiles')
    assert len(instance.visible_save_files) == 2


def test_late_worker_result_cannot_replace_new_folder(app, tmp_path):
    instance, module = app
    first = tmp_path / 'first'
    second = tmp_path / 'second'
    first.mkdir()
    second.mkdir()
    (first / 'HL-02-04.sav').write_bytes(player())
    old_result = SaveBrowser().discover(first)
    stale = Future()
    stale.set_result(old_result)
    instance.save_directory = second
    instance._browser_generation = 2
    instance._poll_save_catalog(stale, 1, first)
    assert instance.save_files == []


def test_pending_refresh_folder_switch_ignores_old_result_and_preserves_no_old_selection(app, tmp_path):
    instance, module = app
    first = tmp_path / 'first'
    second = tmp_path / 'second'
    first.mkdir()
    second.mkdir()
    original = first / 'HL-02-04.sav'
    original.write_bytes(player())
    instance.save_directory = first
    module.App._refresh_save_list(instance)
    instance.current_save_file = original
    pending = Future()
    pending.set_running_or_notify_cancel()
    instance._browser_executor = SimpleNamespace(submit=lambda *args: pending)
    instance.after = Mock(return_value='pending-poll')
    instance.after_cancel = Mock()
    module.App._refresh_save_list(instance)
    old_generation = instance._browser_generation
    instance.save_directory = second
    module.App._refresh_save_list(instance)
    assert instance.current_save_file is None
    assert instance.save_files == []
    pending.set_result(SaveBrowser().discover(first))
    instance._poll_save_catalog(pending, old_generation, first)
    assert instance.save_files == []


def test_edit_worker_pins_source_and_backup_folder_before_selection_changes(app, tmp_path, monkeypatch):
    instance, module = app
    original = tmp_path / 'HL-02-04.sav'
    original.write_bytes(b'original sentinel')
    other = tmp_path / 'HL-02-10.sav'
    other.write_bytes(b'other sentinel')
    backups = tmp_path / 'Backups'
    instance.current_save_file = original
    instance.backup_dir = backups
    instance.temp_dir = tmp_path / 'temp'
    instance.temp_dir.mkdir()
    instance.app_dir = tmp_path
    instance.hlsaves_exe = tmp_path / 'hlsaves.exe'
    instance.hlsaves_exe.write_bytes(b'synthetic executable sentinel')
    instance.hlsge_html = tmp_path / 'editor.html'
    instance._show_progress = Mock()
    instance._hide_progress = Mock()
    instance.winfo_screenwidth = lambda: 1200
    instance.winfo_screenheight = lambda: 800
    targets = []
    def thread(*, target, daemon):
        targets.append(target)
        return SimpleNamespace(start=lambda: None)
    monkeypatch.setattr(module.threading, 'Thread', thread)
    def decompress(args, **kwargs):
        assert Path(args[2]).read_bytes() == b'original sentinel'
        Path(args[3]).write_bytes(b'decompressed sentinel')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(module.subprocess, 'run', decompress)
    monkeypatch.setitem(sys.modules, 'webview', SimpleNamespace())
    launches = []
    def process(*, target, args):
        launches.append(args)
        return SimpleNamespace(start=lambda: None)
    monkeypatch.setattr(module.multiprocessing, 'Process', process)
    instance._extract_and_edit()
    instance.current_save_file = other
    instance.backup_dir = tmp_path / 'other-folder' / 'Backups'
    targets[0]()
    assert len(launches) == 1
    assert launches[0][3] == str(original)
    assert [p.read_bytes() for p in backups.iterdir()] == [b'original sentinel']
    assert (instance.temp_dir / original.name).read_bytes() == b'original sentinel'
    assert not (instance.temp_dir / other.name).exists()
    assert original.read_bytes() == b'original sentinel'
    assert other.read_bytes() == b'other sentinel'


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
