"""Already-uncompressed saves: tagged GVAS and real synthetic SQLite only."""
import errno
from pathlib import Path
import sqlite3
import struct
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tests.test_save_browser import gvas, prop, properties, string
from tests.test_save_integrity import app, extraction  # noqa: F401


def database(label):
    with sqlite3.connect(':memory:') as db:
        db.execute('CREATE TABLE identity(value TEXT)')
        db.execute('INSERT INTO identity VALUES (?)', (label,))
        return db.serialize()


def plain_save(secondary=True, primary=None, exclusive=None):
    primary = database('db1') if primary is None else primary
    exclusive = database('db2') if exclusive is None else exclusive
    arrays = [prop('RawDatabaseImage', 'ArrayProperty', struct.pack('<i', len(primary)) + primary, string('ByteProperty'))]
    if secondary:
        arrays.append(prop('RawExclusiveImage', 'ArrayProperty', struct.pack('<i', len(exclusive)) + exclusive, string('ByteProperty')))
    arrays.append(prop('Opaque', 'ArrayProperty', struct.pack('<i', 7) + b'opaque!', string('ByteProperty')))
    return gvas(properties(*arrays)) + b'opaque tail sentinel'


def test_plain_save_launches_with_exact_snapshot_and_verified_backup(extraction, monkeypatch):
    s = extraction
    payload = plain_save()
    s.source.write_bytes(payload)
    converter = Mock(return_value=SimpleNamespace(returncode=0, stderr=''))
    monkeypatch.setattr(s.module.subprocess, 'run', converter)
    s.instance._extract_and_edit()
    s.threads[0]()
    assert len(s.launches) == 1
    loaded = Path(s.launches[0][1])
    assert loaded.read_bytes() == payload
    assert s.source.read_bytes() == payload
    assert [p.read_bytes() for p in s.instance.backup_dir.iterdir()] == [payload]
    converter.assert_not_called()


@pytest.mark.parametrize('bad_payload', [
    plain_save(primary=b'SQLite format 3\0' + bytes(100)),
    plain_save(exclusive=b'SQLite format 3\0' + bytes(100)),
    plain_save(primary=b'compressed DB bytes'),
    b'GVAS' + bytes(100),
    plain_save()[:-200],
], ids=['bad-primary', 'bad-secondary', 'compressed', 'bad-header', 'truncated'])
def test_corrupt_or_compressed_input_does_not_bypass_missing_converter_output(extraction, monkeypatch, bad_payload):
    s = extraction
    s.source.write_bytes(bad_payload)
    # The converter's warning/success text cannot authorize a fallback.
    monkeypatch.setattr(s.module.subprocess, 'run', Mock(
        return_value=SimpleNamespace(returncode=0, stderr='', stdout='already in uncompressed format')))
    s.instance._extract_and_edit()
    s.threads[0]()
    assert not s.launches
    assert s.source.read_bytes() == bad_payload
    assert list(s.instance.temp_dir.iterdir()) == []


@pytest.mark.parametrize('fault', [errno.ENOSPC, errno.EACCES])
def test_plain_save_staging_failure_preserves_original_and_backup(extraction, monkeypatch, fault):
    s = extraction
    payload = plain_save()
    s.source.write_bytes(payload)
    real_write = s.module.write_new_verified
    def fail_stage(path, data):
        if path.suffix == '.decomp':
            raise OSError(fault, 'injected raw staging failure')
        return real_write(path, data)
    monkeypatch.setattr(s.module, 'write_new_verified', fail_stage)
    monkeypatch.setattr(s.module.subprocess, 'run', Mock(return_value=SimpleNamespace(returncode=0, stderr='')))
    s.instance._extract_and_edit()
    s.threads[0]()
    assert not s.launches
    assert s.source.read_bytes() == payload
    assert [p.read_bytes() for p in s.instance.backup_dir.iterdir()] == [payload]
    assert list(s.instance.temp_dir.iterdir()) == []


def test_empty_secondary_array_is_preserved(extraction, monkeypatch):
    s = extraction
    payload = plain_save(exclusive=b'')
    s.source.write_bytes(payload)
    monkeypatch.setattr(s.module.subprocess, 'run', Mock(return_value=SimpleNamespace(returncode=0, stderr='')))
    s.instance._extract_and_edit()
    s.threads[0]()
    assert len(s.launches) == 1
    assert Path(s.launches[0][1]).read_bytes() == payload


@pytest.mark.parametrize('kind', ['missing-secondary', 'trailing-sqlite-data', 'duplicate-primary', 'opaque-decoy'])
def test_raw_recognizer_rejects_unsupported_or_ambiguous_arrays(kind):
    from src.save_format import is_uncompressed_save
    if kind == 'missing-secondary':
        payload = plain_save(secondary=False)
    elif kind == 'trailing-sqlite-data':
        payload = plain_save(primary=database('db1') + b'extra database bytes')
    elif kind == 'duplicate-primary':
        db = database('db1')
        array = prop('RawDatabaseImage', 'ArrayProperty', struct.pack('<i', len(db)) + db, string('ByteProperty'))
        payload = gvas(properties(array, array))
    else:
        payload = gvas(properties(prop('Opaque', 'ArrayProperty', struct.pack('<i', 16) + b'SQLite format 3\0', string('ByteProperty'))))
    assert not is_uncompressed_save(payload)


@pytest.mark.parametrize('kind', ['reversed-images', 'tag-guid', 'opaque-db-decoy'])
def test_raw_recognizer_rejects_layouts_the_embedded_writer_cannot_preserve(kind):
    from src.save_format import is_uncompressed_save
    first, second = database('db1'), database('db2')
    def array(name, data):
        return prop(name, 'ArrayProperty', struct.pack('<i',len(data))+data, string('ByteProperty'))
    primary, secondary = array('RawDatabaseImage', first), array('RawExclusiveImage', second)
    if kind == 'reversed-images':
        payload = gvas(properties(secondary, primary))
    elif kind == 'tag-guid':
        guid_pos = primary.index(string('ByteProperty')) + len(string('ByteProperty'))
        primary = primary[:guid_pos] + b'\1' + bytes(16) + primary[guid_pos+1:]
        payload = gvas(properties(primary, secondary))
    else:
        decoy = b'RawDatabaseImage' + string('ByteProperty') + b'\0' + struct.pack('<i',len(first)) + first
        payload = gvas(properties(array('Opaque', decoy), primary, secondary))
    assert not is_uncompressed_save(payload)
