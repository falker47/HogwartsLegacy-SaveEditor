"""The packaged executable must never absorb local runtime or save files."""
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / 'scripts/stage_release_assets.py'


def stage(source, destination):
    spec = importlib.util.spec_from_file_location('release_assets', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.stage(source, destination)


def test_only_public_assets_enter_pyinstaller_staging(tmp_path):
    source, destination = tmp_path / 'assets', tmp_path / 'staged'
    source.mkdir()
    expected = {'HLSGE.html', 'hlsaves.exe', 'editor_bridge.js'}
    for name in expected | {'oo2core_9_win64.dll', 'personal.sav', 'config.json'}:
        (source / name).write_bytes(name.encode())
    stage(source, destination)
    assert {p.name for p in destination.iterdir()} == expected
    for name in expected:
        assert (destination / name).read_bytes() == (source / name).read_bytes()


def test_missing_asset_fails_before_creating_staging(tmp_path):
    source, destination = tmp_path / 'assets', tmp_path / 'staged'
    source.mkdir()
    (source / 'HLSGE.html').write_bytes(b'html')
    with pytest.raises(FileNotFoundError):
        stage(source, destination)
    assert not destination.exists()


def test_existing_staging_is_not_reused(tmp_path):
    source, destination = tmp_path / 'assets', tmp_path / 'staged'
    source.mkdir()
    destination.mkdir()
    for name in ('HLSGE.html', 'hlsaves.exe', 'editor_bridge.js'):
        (source / name).write_bytes(b'public')
    sentinel = destination / 'keep'
    sentinel.write_bytes(b'keep')
    with pytest.raises(FileExistsError):
        stage(source, destination)
    assert sentinel.read_bytes() == b'keep'
