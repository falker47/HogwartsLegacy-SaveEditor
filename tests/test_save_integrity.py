"""Fault injection on disposable synthetic saves only; no native converter or GUI."""

import base64
import errno
import os
import shutil
import subprocess
import sys
import textwrap
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.editor import EditorApi
from tests.editor_harness import make_databases, synthetic_save
from tests.test_save_paths import app
from tests.test_wgs_export import build_wgs, snapshot
from src import save_paths
from src.save_io import write_new_verified

REAL_SUBPROCESS_RUN = subprocess.run


@pytest.fixture
def edit(tmp_path, monkeypatch):
    source = tmp_path / 'original.sav'
    source.write_bytes(b'compressed original sentinel')
    loaded = tmp_path / 'loaded.decomp'
    payload = synthetic_save(make_databases(tmp_path))
    loaded.write_bytes(payload)
    status = Mock()
    api = EditorApi(str(loaded), loaded.name, str(source), 'synthetic-converter', str(tmp_path), status)
    calls = []

    def convert(args, **kwargs):
        calls.append(args)
        data = Path(args[2]).read_bytes()
        Path(args[3]).write_bytes(b'COMPRESSED' + data if args[1] == '-c' else data[10:])
        return SimpleNamespace(returncode=0, stderr='')

    monkeypatch.setattr('src.editor.subprocess.run', convert)
    return SimpleNamespace(api=api, source=source, loaded=loaded, payload=payload,
                           status=status, calls=calls, convert=convert, root=tmp_path)


def encoded(data):
    return base64.b64encode(data).decode('ascii')


@pytest.mark.parametrize('fault', ['error', 'permission', 'disk-full', 'missing', 'empty', 'truncated', 'roundtrip'])
def test_converter_fault_keeps_original_byte_exact(edit, monkeypatch, fault):
    s = edit
    before = s.source.read_bytes()

    def failing(args, **kwargs):
        target = Path(args[3])
        if fault == 'permission':
            raise PermissionError(errno.EACCES, 'synthetic denied')
        if fault == 'missing':
            return SimpleNamespace(returncode=0, stderr='')
        target.write_bytes(b'partial' if fault != 'empty' else b'')
        if fault == 'disk-full':
            raise OSError(errno.ENOSPC, 'synthetic disk full')
        if fault == 'error':
            return SimpleNamespace(returncode=1, stderr='synthetic converter failed')
        if fault == 'roundtrip' and args[1] == '-c':
            return s.convert(args, **kwargs)
        return SimpleNamespace(returncode=0, stderr='')

    monkeypatch.setattr('src.editor.subprocess.run', failing)
    result = s.api.save_edited_file(encoded(s.payload))
    assert result['success'] is False
    assert s.source.read_bytes() == before
    assert not any(call.args[0] == 'success' for call in s.status.call_args_list)


def test_success_requires_exact_roundtrip_before_publish(edit):
    s = edit
    assert s.api.save_edited_file(encoded(s.payload)) == {'success': True}
    assert s.source.read_bytes() == b'COMPRESSED' + s.payload
    assert [args[1] for args in s.calls] == ['-c', '-d']
    assert all(Path(args[3]) != s.source for args in s.calls)
    assert s.loaded.read_bytes() == s.payload
    assert not list(s.root.glob('.*.tmp'))
    assert not list(s.root.glob('*.edited'))


@pytest.mark.parametrize('data', ['%%%%', '', encoded(b'corrupt save'), encoded(b'SQLite format 3\0')])
def test_corrupt_bridge_payload_stops_before_converter(edit, data):
    assert edit.api.save_edited_file(data)['success'] is False
    assert edit.source.read_bytes() == b'compressed original sentinel'
    assert edit.calls == []


def test_stale_editor_does_not_overwrite_newer_save(edit):
    edit.source.write_bytes(b'newer external save')
    assert not edit.api.save_edited_file(encoded(edit.payload))['success']
    assert edit.source.read_bytes() == b'newer external save'


@pytest.mark.parametrize('fault', ['short', 'permission', 'disk-full'])
def test_wgs_output_failure_rolls_back_without_source_writes(tmp_path, monkeypatch, fault):
    root, _ = build_wgs(tmp_path, {'a/one': b'HL-02-04 synthetic', 'b/two': b'HL-03-10 synthetic'})
    before = snapshot(root)
    destination = tmp_path / 'exports'
    real_open = Path.open

    class Writer:
        def __init__(self, output): self.output = output
        def __enter__(self): return self
        def __exit__(self, *args): self.output.close()
        def fileno(self): return self.output.fileno()
        def write(self, data):
            count = self.output.write(data[:4])
            if fault == 'disk-full': raise OSError(errno.ENOSPC, 'synthetic disk full')
            return count

    def controlled_open(path, mode='r', *args, **kwargs):
        if mode != 'rb' and path.is_relative_to(root):
            pytest.fail('Production attempted WGS write')
        if path.name == 'HL-03-10.sav' and mode == 'xb':
            if fault == 'permission': raise PermissionError(errno.EACCES, 'synthetic denied')
            return Writer(real_open(path, mode, *args, **kwargs))
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', controlled_open)
    with pytest.raises(OSError):
        save_paths.export_wgs_saves(root, destination)
    assert not list(destination.iterdir())
    assert snapshot(root) == before


@pytest.fixture
def extraction(app, tmp_path, monkeypatch):
    instance, module = app
    source = tmp_path / 'HL-02-04.sav'
    source.write_bytes(b'original source')
    instance.current_save_file = source
    instance.backup_dir = tmp_path / 'Backups'
    instance.temp_dir = tmp_path / 'temp'
    instance.temp_dir.mkdir()
    instance.app_dir = tmp_path
    instance.hlsaves_exe = tmp_path / 'hlsaves.exe'
    instance.hlsaves_exe.write_bytes(b'executable sentinel')
    instance.hlsge_html = tmp_path / 'editor.html'
    instance._show_progress = Mock()
    instance._hide_progress = Mock()
    instance.winfo_screenwidth = lambda: 1200
    instance.winfo_screenheight = lambda: 800
    monkeypatch.setattr(module.messagebox, 'showerror', Mock())
    threads = []
    monkeypatch.setattr(module.threading, 'Thread', lambda **kw: SimpleNamespace(start=lambda: threads.append(kw['target'])))
    import sys
    monkeypatch.setitem(sys.modules, 'webview', SimpleNamespace())
    launches = []
    monkeypatch.setattr(module.multiprocessing, 'Process', lambda **kw:
                        SimpleNamespace(start=lambda: launches.append(kw['args']), is_alive=lambda: False))
    return SimpleNamespace(instance=instance, module=module, source=source, threads=threads, launches=launches)


def test_stale_decompression_cannot_be_loaded_as_current_save(extraction, monkeypatch):
    s = extraction
    stale = s.instance.temp_dir / 'HL-02-04.decomp'
    stale.write_bytes(b'GVAS stale prior session')
    monkeypatch.setattr(s.module.subprocess, 'run', lambda *a, **kw: SimpleNamespace(returncode=0, stderr=''))
    s.instance._extract_and_edit()
    s.threads.pop(0)()
    assert s.launches == []
    assert s.source.read_bytes() == b'original source'


def test_backups_from_same_second_never_overwrite_previous_copy(extraction, monkeypatch):
    s = extraction
    monkeypatch.setattr(s.module, 'datetime', SimpleNamespace(now=lambda: SimpleNamespace(strftime=lambda _: 'fixed-time')))
    def decompress(args, **kwargs):
        Path(args[3]).write_bytes(b'GVAS synthetic decompressed')
        return SimpleNamespace(returncode=0, stderr='')
    monkeypatch.setattr(s.module.subprocess, 'run', decompress)
    for content in (b'original source', b'next source'):
        s.source.write_bytes(content)
        s.instance._extract_and_edit()
        s.threads[-1]()
    assert sorted(p.read_bytes() for p in s.instance.backup_dir.iterdir()) == [b'next source', b'original source']
    assert len({args[1] for args in s.launches}) == 2


def test_raw_database_short_write_is_not_reported_as_success(edit, monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules, 'webview', SimpleNamespace(SAVE_DIALOG=30))
    target = edit.root / 'export.sqlite'
    edit.api.set_window(SimpleNamespace(create_file_dialog=lambda *a, **kw: str(target)))
    real_open = Path.open
    class ShortWriter:
        def __init__(self, output): self.output = output
        def __enter__(self): return self
        def __exit__(self, *args): self.output.close()
        def fileno(self): return self.output.fileno()
        def write(self, data): return self.output.write(data[:20])
    monkeypatch.setattr(Path, 'open', lambda p, mode='r', *a, **kw:
                        ShortWriter(real_open(p, mode, *a, **kw)) if p == target and mode == 'xb'
                        else real_open(p, mode, *a, **kw))
    assert not edit.api.export_database(encoded(b'SQLite format 3\0synthetic'), 'sqldb1.sqlite')['success']
    assert not target.exists()
    assert edit.calls == []


@pytest.mark.parametrize('fault', ['empty', 'corrupt', 'error'])
def test_bad_decompression_never_launches_editor(extraction, monkeypatch, fault):
    s = extraction
    def decompress(args, **kwargs):
        Path(args[3]).write_bytes(b'' if fault == 'empty' else b'corrupt')
        return SimpleNamespace(returncode=int(fault == 'error'), stderr='synthetic error')
    monkeypatch.setattr(s.module.subprocess, 'run', decompress)
    s.instance._extract_and_edit()
    s.threads[0]()
    assert not s.launches
    assert s.source.read_bytes() == b'original source'


@pytest.mark.parametrize('fault', ['permission', 'disk-full'])
def test_atomic_publication_failure_allows_retry(edit, monkeypatch, fault):
    def fail_replace(*args):
        raise OSError(errno.EACCES if fault == 'permission' else errno.ENOSPC, 'synthetic replace failure')
    with monkeypatch.context() as m:
        m.setattr('src.editor.os.replace', fail_replace)
        assert not edit.api.save_edited_file(encoded(edit.payload))['success']
    assert edit.source.read_bytes() == b'compressed original sentinel'
    assert not list(edit.root.glob('.hl-edit-*'))
    assert edit.api.save_edited_file(encoded(edit.payload))['success']


def test_original_changed_during_conversion_is_preserved(edit, monkeypatch):
    def convert(args, **kwargs):
        result = edit.convert(args, **kwargs)
        if args[1] == '-d': edit.source.write_bytes(b'new game save during edit')
        return result
    monkeypatch.setattr('src.editor.subprocess.run', convert)
    assert not edit.api.save_edited_file(encoded(edit.payload))['success']
    assert edit.source.read_bytes() == b'new game save during edit'


def test_extraction_snapshot_prevents_change_before_editor_start(edit):
    snapshot_path = edit.root / 'snapshot.sav'
    snapshot_path.write_bytes(edit.source.read_bytes())
    edit.source.write_bytes(b'new save before webview starts')
    api = EditorApi(str(edit.loaded), edit.loaded.name, str(edit.source), 'synthetic-converter',
                    str(edit.root), original_snapshot=str(snapshot_path))
    assert not api.save_edited_file(encoded(edit.payload))['success']
    assert edit.source.read_bytes() == b'new save before webview starts'
    assert not edit.calls


@pytest.mark.parametrize('phase', ['write', 'flush', 'fsync', 'verify'])
def test_verified_copy_errors_remove_only_new_file(edit, monkeypatch, phase):
    target = edit.root / 'copy.sav'
    data = edit.payload
    real_open, real_read = Path.open, Path.read_bytes
    class Writer:
        def __init__(self, output): self.output = output
        def __enter__(self): return self
        def __exit__(self, *args): self.output.close()
        def fileno(self): return self.output.fileno()
        def write(self, payload):
            if phase == 'write':
                self.output.write(payload[:10])
                raise OSError(errno.ENOSPC, 'synthetic full disk')
            return self.output.write(payload)
        def flush(self):
            if phase == 'flush': raise OSError(errno.ENOSPC, 'synthetic flush failure')
            return self.output.flush()
    monkeypatch.setattr(Path, 'open', lambda p, mode='r', *a, **kw:
                        Writer(real_open(p, mode, *a, **kw)) if p == target and mode == 'xb'
                        else real_open(p, mode, *a, **kw))
    if phase == 'fsync': monkeypatch.setattr(os, 'fsync', Mock(side_effect=OSError('synthetic sync failure')))
    if phase == 'verify': monkeypatch.setattr(Path, 'read_bytes', lambda p: b'wrong bytes' if p == target else real_read(p))
    with pytest.raises(OSError): write_new_verified(target, data)
    assert not target.exists()
    assert edit.source.read_bytes() == b'compressed original sentinel'


def test_exclusive_verified_copy_does_not_overwrite_existing_file(tmp_path):
    target = tmp_path / 'existing.sav'
    target.write_bytes(b'keep existing')
    with pytest.raises(FileExistsError): write_new_verified(target, b'new copy')
    assert target.read_bytes() == b'keep existing'


def test_backup_failure_stops_before_decompression(extraction, monkeypatch):
    s = extraction
    converter = Mock()
    monkeypatch.setattr(s.module.subprocess, 'run', converter)
    monkeypatch.setattr(s.module, 'write_new_verified', Mock(side_effect=PermissionError('synthetic backup denied')))
    s.instance._extract_and_edit()
    s.threads[0]()
    assert not s.launches
    converter.assert_not_called()
    assert s.source.read_bytes() == b'original source'


def test_backup_can_restore_disposable_copy_byte_for_byte(extraction, monkeypatch):
    s = extraction
    monkeypatch.setattr(s.module.subprocess, 'run', lambda *a, **kw: SimpleNamespace(returncode=1, stderr='synthetic corrupt input'))
    s.instance._extract_and_edit()
    s.threads[0]()
    backup, = s.instance.backup_dir.iterdir()
    assert backup.read_bytes() == s.source.read_bytes()
    s.source.write_bytes(b'disposable edited bytes')
    # The product exposes Open Backups, not a restore API; reproduce manual copy only.
    shutil.copyfile(backup, s.source)
    assert s.source.read_bytes() == b'original source'
    assert not list(s.instance.temp_dir.iterdir())


def test_terminated_converter_cannot_truncate_original(edit):
    code = textwrap.dedent('''
        import base64, os, sys
        from pathlib import Path
        from src.editor import EditorApi
        import src.editor as editor
        root = Path(sys.argv[1])
        def interrupted(args, **kwargs):
            Path(args[3]).write_bytes(b'partial converter output')
            os._exit(86)
        editor.subprocess.run = interrupted
        api = EditorApi(str(root / 'loaded.decomp'), 'loaded.decomp', str(root / 'original.sav'),
                        'synthetic-converter', str(root))
        api.save_edited_file(base64.b64encode((root / 'loaded.decomp').read_bytes()).decode())
    ''')
    result = REAL_SUBPROCESS_RUN([sys.executable, '-c', code, str(edit.root)],
                            cwd=Path(__file__).resolve().parents[1], stdin=subprocess.DEVNULL,
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 86, result.stderr
    assert edit.source.read_bytes() == b'compressed original sentinel'
    # Hard termination skips Python cleanup. An orphan is allowed, never reused.
    orphan, = edit.root.glob('.hl-edit-*')
    assert (orphan / 'candidate.sav').read_bytes() == b'partial converter output'
    assert edit.api.save_edited_file(encoded(edit.payload))['success']
    assert edit.source.read_bytes() == b'COMPRESSED' + edit.payload


def test_wgs_destination_verification_failure_rolls_back(tmp_path, monkeypatch):
    root, _ = build_wgs(tmp_path, {'a/one': b'HL-02-04 synthetic'})
    before = snapshot(root)
    destination = tmp_path / 'exports'
    real_read = Path.read_bytes
    monkeypatch.setattr(Path, 'read_bytes', lambda p: b'bad destination' if p.parent == destination else real_read(p))
    with pytest.raises(OSError, match='verification'): save_paths.export_wgs_saves(root, destination)
    assert not list(destination.iterdir())
    assert snapshot(root) == before


def test_status_failure_does_not_report_committed_save_as_failed(edit):
    edit.api.status_callback = Mock(side_effect=OSError('synthetic status disk full'))
    assert edit.api.save_edited_file(encoded(edit.payload))['success']
    assert edit.source.read_bytes() == b'COMPRESSED' + edit.payload


def test_cleanup_failure_does_not_report_committed_save_as_failed(edit, monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(shutil, 'rmtree', Mock(side_effect=PermissionError('synthetic cleanup denied')))
        result = edit.api.save_edited_file(encoded(edit.payload))
        assert result['success']
        assert 'cleanup' in result.get('warning', '').lower()
    assert edit.source.read_bytes() == b'COMPRESSED' + edit.payload


def test_wgs_catchable_interruption_rolls_back_all_outputs(tmp_path, monkeypatch):
    root, _ = build_wgs(tmp_path, {'a/one': b'HL-02-04 synthetic', 'b/two': b'HL-03-10 synthetic'})
    before = snapshot(root)
    destination = tmp_path / 'exports'
    real_open = Path.open
    class InterruptedWriter:
        def __init__(self, output): self.output = output
        def __enter__(self): return self
        def __exit__(self, *args): self.output.close()
        def fileno(self): return self.output.fileno()
        def write(self, data):
            self.output.write(data[:4])
            raise KeyboardInterrupt('synthetic interrupted write')
    monkeypatch.setattr(Path, 'open', lambda p, mode='r', *a, **kw:
                        InterruptedWriter(real_open(p, mode, *a, **kw)) if p.name == 'HL-03-10.sav' and mode == 'xb'
                        else real_open(p, mode, *a, **kw))
    with pytest.raises(KeyboardInterrupt): save_paths.export_wgs_saves(root, destination)
    assert not list(destination.iterdir())
    assert snapshot(root) == before


def test_overlapping_call_is_refused_while_session_is_saving(edit, monkeypatch):
    second_payload = edit.payload + b'second edited tail'
    entered = False
    def convert(args, **kwargs):
        nonlocal entered
        if not entered:
            entered = True
            assert not edit.api.save_edited_file(encoded(second_payload))['success']
        return edit.convert(args, **kwargs)
    monkeypatch.setattr('src.editor.subprocess.run', convert)
    assert edit.api.save_edited_file(encoded(edit.payload))['success']
    assert edit.source.read_bytes() == b'COMPRESSED' + edit.payload


def test_two_threads_cannot_both_publish_from_one_editor_session(edit, monkeypatch):
    ready, release = threading.Event(), threading.Event()
    real_replace = os.replace
    results = {}
    worker = None
    def controlled_replace(source, destination):
        if threading.current_thread() is worker:
            ready.set()
            assert release.wait(5), 'Second save did not complete'
        return real_replace(source, destination)
    monkeypatch.setattr('src.editor.os.replace', controlled_replace)
    worker = threading.Thread(target=lambda: results.update(first=edit.api.save_edited_file(encoded(edit.payload))))
    worker.start()
    try:
        assert ready.wait(5), 'First save did not reach publication'
        results['second'] = edit.api.save_edited_file(encoded(edit.payload + b'second tail'))
    finally:
        release.set()
        worker.join(5)
    assert not worker.is_alive()
    assert results['first']['success']
    assert results['second']['success'] is False
    assert edit.source.read_bytes() == b'COMPRESSED' + edit.payload


@pytest.mark.parametrize('cleanup_fails', [False, True])
def test_editor_closure_cleans_only_its_session_and_reports_failure(extraction, monkeypatch, cleanup_fails):
    s = extraction
    def decompress(args, **kwargs):
        Path(args[3]).write_bytes(b'GVAS disposable payload')
        return SimpleNamespace(returncode=0, stderr='')
    monkeypatch.setattr(s.module.subprocess, 'run', decompress)
    unrelated = s.instance.temp_dir / 'other-session'
    unrelated.mkdir()
    (unrelated / 'keep').write_bytes(b'other session input')
    s.instance._extract_and_edit()
    s.threads[0]()
    session_dir = Path(s.launches[0][1]).parent
    assert session_dir.exists()
    if cleanup_fails:
        monkeypatch.setattr(s.module.shutil, 'rmtree', Mock(side_effect=PermissionError('synthetic cleanup denied')))
    s.threads[1]()
    assert session_dir.exists() is cleanup_fails
    assert (unrelated / 'keep').read_bytes() == b'other session input'
    if cleanup_fails:
        assert any('cleanup' in str(call).lower() for call in s.instance._log.call_args_list)
    assert s.source.read_bytes() == b'original source'
