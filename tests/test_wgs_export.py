"""Synthetic WGS acceptance; no real saves or account identifiers."""
from concurrent.futures import Future
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src import save_paths as paths
from src.save_browser import SaveBrowser, format_entry, profile_labels
from tests.test_save_browser import STAMP, character, directory, gvas, properties, structure
from tests.test_save_paths import app  # shared headless App fixture


def build_wgs(tmp_path, payloads=None):
    root = tmp_path / 'Packages/WarnerBros.Interactive.PHX_ktmk1xygcecda/SystemAppData/wgs'
    user = root / 'synthetic-user'
    user.mkdir(parents=True)
    (user / 'containers.index').write_bytes(b'index sentinel HL-99-99')
    for name, data in (payloads or {}).items():
        target = user / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return root, user


def snapshot(root):
    return {str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}


def player_payload():
    return gvas(properties(character(), structure('DirectoryEntry', 'SaveDirectoryEntry', directory())))


def test_exactly_one_user_resolved_by_index(tmp_path):
    root, user = build_wgs(tmp_path)
    (root / 'unrelated-folder').mkdir()
    assert paths.find_wgs_user_directory(root) == user


@pytest.mark.parametrize('mode', ['missing-root', 'missing-index', 'multiple'])
def test_user_resolution_fails_closed(tmp_path, mode):
    root, user = build_wgs(tmp_path)
    if mode == 'missing-root':
        root = tmp_path / 'missing'
    elif mode == 'missing-index':
        (user / 'containers.index').unlink()
    else:
        second = root / 'second-user'
        second.mkdir()
        (second / 'containers.index').write_bytes(b'index')
    with pytest.raises(ValueError, match='exist|containers.index|ambiguous'):
        paths.find_wgs_user_directory(root)


def test_discovery_ignores_metadata_and_limits_container_depth(tmp_path):
    root, user = build_wgs(tmp_path, {
        'container/payload': b'GVAS synthetic HL-03-10 body',
        'container/container.1': b'metadata HL-03-10 different',
        'container/containers.index': b'index HL-03-10 different',
        'container/no-tag': b'not a save',
        'container/deeper/decoy': b'HL-03-10 different',
        'root-file': b'HL-03-10 different',
    })
    assert paths.discover_wgs_save_payloads(root) == {'HL-03-10': user / 'container/payload'}


def test_duplicate_bytes_deduplicated(tmp_path):
    root, user = build_wgs(tmp_path, {'a/one': b'HL-03-10 payload', 'b/two': b'HL-03-10 payload'})
    assert paths.discover_wgs_save_payloads(root) == {'HL-03-10': user / 'a/one'}


@pytest.mark.parametrize('payloads', [
    {'a/one': b'HL-03-10 first', 'b/two': b'HL-03-10 different'},
    {'a/one': b'HL-03-10 HL-03-11'},
])
def test_conflicting_payloads_or_internal_tags_fail_before_export(tmp_path, payloads):
    root, _ = build_wgs(tmp_path, payloads)
    before = snapshot(root)
    destination = tmp_path / 'exports'
    with pytest.raises(ValueError, match='ambiguous'):
        paths.export_wgs_saves(root, destination)
    assert not destination.exists()
    assert snapshot(root) == before


@pytest.mark.parametrize('invalid', [b'HL-03-100', b'XHL-03-10', b'HL-003-10', b'HL-03-10X', b''])
def test_only_complete_save_identifiers_accepted(tmp_path, invalid):
    root, _ = build_wgs(tmp_path, {'a/payload': invalid})
    with pytest.raises(ValueError, match='No unambiguous'):
        paths.discover_wgs_save_payloads(root)


def test_repeated_same_tag_is_one_identity(tmp_path):
    root, user = build_wgs(tmp_path, {'a/payload': b'HL-03-10 HL-03-10'})
    assert paths.discover_wgs_save_payloads(root) == {'HL-03-10': user / 'a/payload'}


def test_oversized_empty_unreadable_ignored_and_reads_bounded(tmp_path, monkeypatch):
    root, user = build_wgs(tmp_path, {
        'a/valid': b'HL-03-10', 'a/empty': b'', 'a/large': b'HL-03-11' + bytes(100),
        'a/unreadable': b'HL-03-12', 'a/growing': b'HL-03-13',
    })
    monkeypatch.setattr(paths, 'MAX_WGS_PAYLOAD_SIZE', 32)
    original_open = Path.open
    class GrowingReader:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, size=-1):
            assert 0 < size <= 33
            return b'HL-03-13' + bytes(size - 8)
    def controlled_open(self, *args, **kwargs):
        if self.name == 'unreadable': raise PermissionError('synthetic unreadable payload')
        if self.name == 'large': pytest.fail('Oversized payload must not be opened')
        if self.name == 'growing': return GrowingReader()
        return original_open(self, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', controlled_open)
    assert paths.discover_wgs_save_payloads(root) == {'HL-03-10': user / 'a/valid'}


def test_byte_exact_export_preserves_entire_source_and_current_browser(tmp_path):
    data = player_payload()
    root, _ = build_wgs(tmp_path, {'a/payload': data, 'a/container.1': b'metadata'})
    before = snapshot(root)
    destination = tmp_path / 'exports'
    outputs = paths.export_wgs_saves(root, destination)
    assert outputs == [destination / 'HL-02-04.sav']
    assert outputs[0].read_bytes() == data
    assert snapshot(root) == before
    entry, = SaveBrowser().discover(destination).entries
    assert entry.path == outputs[0]
    assert entry.character_name == 'Ada Example'
    assert entry.internal_timestamp == STAMP
    assert entry.playtime_seconds == 165600
    assert entry.save_kind == 'manual'
    assert profile_labels([entry])['Profile 2'] == 'Profile 2 — Ada Example'
    assert 'Cragcroftshire' in format_entry(entry).summary


def test_existing_target_refuses_entire_export(tmp_path):
    root, _ = build_wgs(tmp_path, {'a/one': b'HL-02-04 first', 'b/two': b'HL-03-10 second'})
    before = snapshot(root)
    destination = tmp_path / 'exports'
    destination.mkdir()
    (destination / 'HL-03-10.sav').write_bytes(b'existing sentinel')
    with pytest.raises(ValueError, match='already contains'):
        paths.export_wgs_saves(root, destination)
    assert snapshot(destination).keys() == {'HL-03-10.sav'}
    assert (destination / 'HL-03-10.sav').read_bytes() == b'existing sentinel'
    assert snapshot(root) == before


def test_partial_write_failure_removes_all_new_outputs_only(tmp_path, monkeypatch):
    root, _ = build_wgs(tmp_path, {'a/one': b'HL-02-04 first', 'b/two': b'HL-03-10 second'})
    before = snapshot(root)
    destination = tmp_path / 'exports'
    destination.mkdir()
    keep = destination / 'unrelated.txt'
    keep.write_bytes(b'keep')
    original_open = Path.open
    class FailingWriter:
        def __init__(self, output): self.output = output
        def __enter__(self): return self
        def __exit__(self, *args): self.output.close()
        def fileno(self): return self.output.fileno()
        def write(self, data):
            self.output.write(data[:4])
            raise OSError('synthetic disk full')
    def controlled_open(self, mode='r', *args, **kwargs):
        output = original_open(self, mode, *args, **kwargs)
        if self.name == 'HL-03-10.sav' and mode == 'xb': return FailingWriter(output)
        return output
    monkeypatch.setattr(Path, 'open', controlled_open)
    with pytest.raises(OSError, match='disk full'):
        paths.export_wgs_saves(root, destination)
    assert list(destination.iterdir()) == [keep]
    assert keep.read_bytes() == b'keep'
    assert snapshot(root) == before


def test_target_created_after_preflight_is_never_overwritten_or_deleted(tmp_path, monkeypatch):
    root, _ = build_wgs(tmp_path, {'a/one': b'HL-02-04 first', 'b/two': b'HL-03-10 second'})
    destination = tmp_path / 'exports'
    original_open = Path.open
    def racing_open(self, mode='r', *args, **kwargs):
        if self.name == 'HL-03-10.sav' and mode == 'xb':
            with original_open(self, 'wb') as output: output.write(b'concurrent sentinel')
        return original_open(self, mode, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', racing_open)
    with pytest.raises((ValueError, FileExistsError), match='exist|contains'):
        paths.export_wgs_saves(root, destination)
    assert [p.name for p in destination.iterdir()] == ['HL-03-10.sav']
    assert (destination / 'HL-03-10.sav').read_bytes() == b'concurrent sentinel'


@pytest.mark.parametrize('relative', ['', 'new', 'synthetic-user', 'synthetic-user/a/new'])
def test_export_destination_inside_wgs_refused_even_for_copied_root(tmp_path, relative):
    root, _ = build_wgs(tmp_path, {'a/one': b'HL-02-04'})
    copied = tmp_path / 'copied-root'
    root.rename(copied)
    before = snapshot(copied)
    with pytest.raises(ValueError, match='WGS|Game Pass'):
        paths.export_wgs_saves(copied, copied / relative)
    assert snapshot(copied) == before


def test_payload_changed_after_discovery_refuses_export(tmp_path, monkeypatch):
    root, user = build_wgs(tmp_path, {'a/one': b'HL-02-04 first'})
    destination = tmp_path / 'exports'
    original_mkdir = Path.mkdir
    def mutate_source(self, *args, **kwargs):
        if self == destination: (user / 'a/one').write_bytes(b'HL-02-04 changed')
        return original_mkdir(self, *args, **kwargs)
    monkeypatch.setattr(Path, 'mkdir', mutate_source)
    with pytest.raises(ValueError, match='changed'):
        paths.export_wgs_saves(root, destination)
    assert not list(destination.iterdir())


def test_app_export_selects_current_browser_and_persists_manual_folder(app, tmp_path, monkeypatch):
    instance, module = app
    root, _ = build_wgs(tmp_path, {'a/payload': player_payload()})
    before = snapshot(root)
    destination = tmp_path / 'exports'
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path))
    monkeypatch.setattr(module.filedialog, 'askdirectory', lambda **_: str(destination))
    monkeypatch.setattr(module.messagebox, 'showinfo', Mock())
    monkeypatch.setattr(module.messagebox, 'showerror', Mock())
    instance._show_progress = Mock()
    instance._hide_progress = Mock()
    instance._refresh_save_list = lambda: module.App._refresh_save_list(instance)
    instance._export_game_pass_saves()
    assert instance.save_directory == destination.resolve()
    assert instance.config['save_directory'] == str(destination.resolve())
    assert instance.config['auto_detect_saves'] is False
    assert instance.selected_profile == 'Profile 2'
    entry, = instance.save_files
    assert entry.path == destination / 'HL-02-04.sav'
    assert entry.character_name == 'Ada Example'
    assert snapshot(root) == before
    assert 'cloud' in module.messagebox.showinfo.call_args.args[1]
    module.messagebox.showerror.assert_not_called()


@pytest.mark.parametrize('ordinary_base_exists', [False, True])
@pytest.mark.parametrize('has_wgs', [False, True])
def test_auto_detection_explains_export_or_browse(app, tmp_path, monkeypatch, ordinary_base_exists, has_wgs):
    instance, _ = app
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path))
    if has_wgs: build_wgs(tmp_path)
    if ordinary_base_exists: (tmp_path / 'Hogwarts Legacy/Saved/SaveGames').mkdir(parents=True)
    assert not instance._detect_save_directory()
    message = instance.path_label.configure.call_args.kwargs['text']
    assert ('Game Pass' in message and 'Export Game Pass Saves' in message) if has_wgs else (
        'No supported save folder' in message and 'Browse' in message)
    assert instance.save_directory is None
    assert instance.backup_dir is None



def test_unrelated_game_is_not_detected(tmp_path):
    (tmp_path / 'Packages/Other.Game/SystemAppData/wgs').mkdir(parents=True)
    assert paths.find_hogwarts_wgs(str(tmp_path)) is None


@pytest.mark.parametrize('kind', ['user', 'container', 'payload', 'destination'])
def test_links_cannot_expand_scan_or_export_into_wgs(tmp_path, kind):
    root, user = build_wgs(tmp_path, {'a/one': b'HL-02-04'})
    outside = tmp_path / 'unrelated'
    outside.mkdir()
    (outside / 'containers.index').write_bytes(b'index')
    (outside / 'payload').write_bytes(b'HL-02-04 conflicting decoy')
    link = {'user': root / 'linked-user', 'container': user / 'linked-container',
            'payload': user / 'a/linked-payload', 'destination': tmp_path / 'exports'}[kind]
    target = outside / 'payload' if kind == 'payload' else root if kind == 'destination' else outside
    try:
        link.symlink_to(target, target_is_directory=kind != 'payload')
    except OSError:
        pytest.skip('Symbolic links require Windows Developer Mode or elevation')
    before = snapshot(root)
    if kind == 'destination':
        with pytest.raises(ValueError, match='Game Pass'):
            paths.export_wgs_saves(root, link / 'new')
    else:
        assert paths.discover_wgs_save_payloads(root) == {'HL-02-04': user / 'a/one'}
    assert snapshot(root) == before
    assert (outside / 'payload').read_bytes() == b'HL-02-04 conflicting decoy'


@pytest.mark.parametrize('reason', ['busy', 'cancelled', 'not-detected'])
def test_app_noop_export_keeps_previous_folder(app, tmp_path, monkeypatch, reason):
    instance, module = app
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path))
    if reason != 'not-detected': build_wgs(tmp_path, {'a/one': b'HL-02-04'})
    instance.save_directory = tmp_path / 'previous'
    instance.is_working = reason == 'busy'
    monkeypatch.setattr(module.filedialog, 'askdirectory', lambda **_: '')
    monkeypatch.setattr(module.messagebox, 'showinfo', Mock())
    instance._export_game_pass_saves()
    assert instance.save_directory == tmp_path / 'previous'
    instance._save_config.assert_not_called()
    instance._refresh_save_list.assert_not_called()


@pytest.mark.parametrize('fails', [False, True])
def test_app_export_waits_for_worker_before_selecting_folder(app, tmp_path, monkeypatch, fails):
    instance, module = app
    root, _ = build_wgs(tmp_path, {'a/one': player_payload()})
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path))
    destination = tmp_path / 'exports'
    monkeypatch.setattr(module.filedialog, 'askdirectory', lambda **_: str(destination))
    monkeypatch.setattr(module.messagebox, 'showinfo', Mock())
    monkeypatch.setattr(module.messagebox, 'showerror', Mock())
    previous = tmp_path / 'previous'
    instance.save_directory = previous
    future = Future()
    instance._browser_executor = SimpleNamespace(submit=lambda *args: future)
    callbacks = []
    instance.after = lambda delay, callback: callbacks.append(callback) or 'export-poll'
    instance._show_progress = Mock()
    instance._hide_progress = Mock()
    instance._export_game_pass_saves()
    assert not destination.exists()
    assert instance.save_directory == previous
    assert instance._export_poll_id == 'export-poll'
    if fails:
        future.set_exception(OSError('synthetic failure'))
    else:
        future.set_result(paths.export_wgs_saves(root, destination))
    callbacks.pop()()
    assert instance._export_poll_id is None
    if fails:
        assert instance.save_directory == previous
        instance._save_config.assert_not_called()
        assert 'synthetic failure' in module.messagebox.showerror.call_args.args[1]
    else:
        assert instance.save_directory == destination
        assert (destination / 'HL-02-04.sav').read_bytes() == player_payload()



def test_rollback_preserves_output_replaced_by_another_process(tmp_path, monkeypatch):
    root, _ = build_wgs(tmp_path, {'a/one': b'HL-02-04 first', 'b/two': b'HL-03-10 second'})
    destination = tmp_path / 'exports'
    replacement = tmp_path / 'replacement'
    replacement.write_bytes(b'concurrent replacement')
    original_open = Path.open
    class ReplacingWriter:
        def __init__(self, output): self.output = output
        def __enter__(self): return self
        def __exit__(self, *args): self.output.close()
        def fileno(self): return self.output.fileno()
        def write(self, data):
            replacement.replace(destination / 'HL-02-04.sav')
            self.output.write(data[:4])
            raise OSError('synthetic disk full')
    def controlled_open(self, mode='r', *args, **kwargs):
        output = original_open(self, mode, *args, **kwargs)
        if self.name == 'HL-03-10.sav' and mode == 'xb': return ReplacingWriter(output)
        return output
    monkeypatch.setattr(Path, 'open', controlled_open)
    with pytest.raises(OSError, match='disk full'):
        paths.export_wgs_saves(root, destination)
    assert (destination / 'HL-02-04.sav').read_bytes() == b'concurrent replacement'
    assert not (destination / 'HL-03-10.sav').exists()
