"""Generated GVAS metadata only: no game databases or personal save data."""

import os
import struct
from datetime import datetime, timedelta, timezone

import pytest

from src import save_browser as browser


def string(value):
    raw = value.encode('utf-8') + b'\0'
    return struct.pack('<i', len(raw)) + raw


def prop(name, kind, payload=b'', extra=b''):
    return string(name) + string(kind) + struct.pack('<ii', len(payload), 0) + extra + b'\0' + payload


def properties(*values):
    return b''.join(values) + string('None')


def structure(name, struct_type, payload):
    return prop(name, 'StructProperty', payload, string(struct_type) + bytes(16))


def ticks(value):
    delta = value - datetime(1, 1, 1, tzinfo=timezone.utc)
    return (delta.days * 86400 + delta.seconds) * 10_000_000 + delta.microseconds * 10


STAMP = datetime(2025, 2, 3, 18, 40, tzinfo=timezone.utc)


def directory(stem='HL-02-04', kind='USER', stamp=STAMP, location='RegionNameHelmsdale', used=True):
    return properties(
        prop('FilenameSlot', 'StrProperty', string(stem)),
        prop('CharacterID', 'IntProperty', struct.pack('<i', 2)),
        prop('SaveType', 'EnumProperty', string('ESaveType::' + kind), string('ESaveType')),
        prop('bIsUsed', 'BoolProperty', extra=bytes([used])),
        structure('GameTime', 'DateTime', struct.pack('<q', 46 * 3600 * 10_000_000)),
        structure('SaveTime', 'DateTime', struct.pack('<q', ticks(stamp))),
        prop('CurrentMap', 'StrProperty', string(location)),
    )


def gvas(payload, manifest=False):
    cls = 'PersistentGameDataList' if manifest else 'PersistentGameData'
    return (b'GVAS' + struct.pack('<iiHHHI', 2, 524, 4, 27, 2, 123)
            + string('synthetic') + struct.pack('<ii', 3, 0)
            + string('/Script/PersistentData.' + cls) + payload + bytes(4))


def player(**kwargs):
    # A compressed payload deliberately contains decoy property text. The reader
    # must skip it by length, never scan for a field name in database bytes.
    decoy = b'not-a-database' + directory(stem='HL-99-99')
    return gvas(properties(
        prop('RawDatabaseImage', 'ArrayProperty', struct.pack('<i', len(decoy)) + decoy, string('ByteProperty')),
        structure('DirectoryEntry', 'SaveDirectoryEntry', directory(**kwargs)),
    ))


def manifest(*rows):
    items = b''.join(rows)
    array = (struct.pack('<i', len(rows)) + string('SaveFileList') + string('StructProperty')
             + struct.pack('<q', len(items)) + string('SaveDirectoryEntry') + bytes(17) + items)
    return gvas(properties(structure('Info', 'PersistentGameDataListInfo', properties(
        prop('bIsValid', 'BoolProperty', extra=b'\1'),
        prop('SaveFileList', 'ArrayProperty', array, string('StructProperty')),
    ))), manifest=True)


def write(tmp_path, name, data, mtime=100):
    path = tmp_path / name
    path.write_bytes(data)
    os.utime(path, (mtime, mtime))
    return path


def test_excludes_system_and_unknown_nonplayer_but_keeps_manual_auto_and_renamed_player(tmp_path):
    for name in ['SaveGameList.sav', 'SavedUserOptions.sav', 'other.sav']:
        write(tmp_path, name, b'support data')
    for name in ['HL-02-00.sav', 'HL-02-04.sav', 'HL-02-10.sav', 'HL-02-14.sav', 'renamed.sav']:
        write(tmp_path, name, player())
    catalog = browser.SaveBrowser().discover(tmp_path)
    assert {e.filename for e in catalog.entries} == {
        'HL-02-00.sav', 'HL-02-04.sav', 'HL-02-10.sav', 'HL-02-14.sav', 'renamed.sav'}
    assert all(e.editable for e in catalog.entries)
    assert len(catalog.excluded) == 3


def test_reads_manifest_and_individual_metadata_without_decompression(tmp_path):
    path = write(tmp_path, 'HL-02-04.sav', player())
    write(tmp_path, 'SaveGameList.sav', manifest(directory()))
    entry = browser.SaveBrowser().discover(tmp_path).entries[0]
    assert entry.path == path
    assert entry.filename == 'HL-02-04.sav'
    assert entry.save_kind == 'manual'
    assert entry.slot == 2
    assert entry.internal_timestamp == STAMP
    assert entry.playtime_seconds == 165600
    assert entry.location_id == 'RegionNameHelmsdale'
    assert entry.metadata_source == 'SaveGameList.sav'
    assert entry.metadata_status == 'complete'


def test_semantic_timestamp_beats_mtime_and_array_order(tmp_path):
    older = directory(stem='HL-02-04')
    newer = directory(stem='HL-02-10', kind='AUTO', stamp=STAMP + timedelta(hours=1))
    write(tmp_path, 'SaveGameList.sav', manifest(older, newer))
    write(tmp_path, 'HL-02-04.sav', player(), mtime=9999)
    write(tmp_path, 'HL-02-10.sav', player(stem='HL-02-10', kind='AUTO', stamp=STAMP + timedelta(hours=1)), mtime=1)
    entries = browser.SaveBrowser().discover(tmp_path).entries
    assert [e.filename for e in entries] == ['HL-02-10.sav', 'HL-02-04.sav']
    assert entries[0].autosave_index == 10


def test_corrupt_player_metadata_kept_and_fallback_sort_is_deterministic(tmp_path):
    for name in ['HL-02-12.sav', 'HL-02-11.sav', 'HL-02-04.sav']:
        write(tmp_path, name, b'broken')
    write(tmp_path, 'HL-02-10.sav', player(stem='HL-02-10', kind='AUTO'), mtime=1)
    catalog = browser.SaveBrowser().discover(tmp_path)
    assert [e.filename for e in catalog.entries] == ['HL-02-10.sav', 'HL-02-04.sav', 'HL-02-11.sav', 'HL-02-12.sav']
    assert catalog.entries[1].save_kind == 'manual'
    assert catalog.entries[1].metadata_status == 'fallback'
    assert catalog.warnings


def test_stale_manifest_and_renamed_identity_never_redirect_selection(tmp_path):
    write(tmp_path, 'SaveGameList.sav', manifest(directory(stamp=STAMP + timedelta(days=7))))
    path = write(tmp_path, 'HL-02-04.sav', player())
    renamed = write(tmp_path, 'custom.sav', player(stem='HL-02-10', kind='AUTO'))
    catalog = browser.SaveBrowser().discover(tmp_path)
    entry = next(e for e in catalog.entries if e.path == path)
    assert entry.internal_timestamp == STAMP
    assert entry.metadata_source == 'DirectoryEntry'
    assert entry.metadata_status == 'index mismatch'
    assert next(e for e in catalog.entries if e.filename == 'custom.sav').path == renamed


def test_cache_reuses_unchanged_reads_and_invalidates_file_and_manifest(tmp_path, monkeypatch):
    path = write(tmp_path, 'HL-02-04.sav', player())
    index = write(tmp_path, 'SaveGameList.sav', manifest(directory()))
    service = browser.SaveBrowser()
    reads = []
    read = browser.read_metadata
    def track(path):
        reads.append(path.name)
        return read(path)
    monkeypatch.setattr(browser, 'read_metadata', track)
    service.discover(tmp_path)
    service.discover(tmp_path)
    assert reads == ['SaveGameList.sav', 'HL-02-04.sav']
    path.write_bytes(player(location='Hamlet_Aranshire'))
    result = service.discover(tmp_path)
    assert result.entries[0].location_id == 'Hamlet_Aranshire'
    assert len(reads) == 3
    index.write_bytes(manifest(directory(location='Hamlet_Aranshire')))
    assert service.discover(tmp_path).entries[0].metadata_source == 'SaveGameList.sav'
    assert len(reads) == 4


def test_card_and_info_formatting_use_game_time_current_offset_and_verified_locations(tmp_path):
    write(tmp_path, 'HL-02-10.sav', player(stem='HL-02-10', kind='AUTO', location='Overland'))
    entry = browser.SaveBrowser().discover(tmp_path).entries[0]
    display = browser.format_entry(entry, tz=timezone(timedelta(hours=2)))
    assert display.title == 'Autosave'
    assert display.summary == '46h | The Highlands'
    assert display.date == '03 Feb 2025, 20:40'
    assert display.technical == 'HL-02-10.sav · Profile 2'
    assert 'UTC' in display.details
    assert 'Filesystem modified' in display.details
    assert browser.format_entry(entry, locale='it').summary == '46h | Le Highlands'


def test_unknown_location_and_missing_metadata_are_labelled(tmp_path):
    write(tmp_path, 'HL-02-04.sav', player(location='Unknown_Internal_ID'))
    write(tmp_path, 'HL-02-11.sav', b'broken')
    entries = browser.SaveBrowser().discover(tmp_path).entries
    normal = browser.format_entry(entries[0])
    fallback = browser.format_entry(entries[1])
    assert normal.title == 'Manual Save'
    assert normal.summary == '46h | Location unavailable'
    assert 'Location ID: Unknown_Internal_ID' in normal.details
    assert 'Unknown_Internal_ID' not in normal.summary
    assert fallback.summary == 'Playtime unavailable | Location unavailable'
    assert fallback.date.startswith('File modified: ')
    assert 'fallback' in fallback.details.lower()


@pytest.mark.parametrize('data', [b'', b'GVAS', player()[:-30], b'GVAS' + bytes(100)])
def test_malformed_format_is_bounded_and_does_not_crash_discovery(tmp_path, data):
    write(tmp_path, 'HL-02-04.sav', data)
    write(tmp_path, 'HL-02-10.sav', player(stem='HL-02-10', kind='AUTO'))
    assert len(browser.SaveBrowser().discover(tmp_path).entries) == 2


def test_index_used_flag_does_not_hide_existing_editable_save(tmp_path):
    write(tmp_path, 'HL-02-04.sav', player())
    write(tmp_path, 'SaveGameList.sav', manifest(directory(used=False)))
    entry = browser.SaveBrowser().discover(tmp_path).entries[0]
    assert entry.editable
    assert entry.metadata_source == 'DirectoryEntry'
    assert entry.metadata_status == 'not indexed'


def test_recognized_class_survives_optional_metadata_failure(tmp_path):
    write(tmp_path, 'renamed.sav', player()[:-30])
    write(tmp_path, 'HL-02-04.sav', manifest(directory())[:-30])
    catalog = browser.SaveBrowser().discover(tmp_path)
    assert [e.filename for e in catalog.entries] == ['renamed.sav']
    assert catalog.entries[0].metadata_status == 'fallback'
    assert catalog.warnings
    assert ('HL-02-04.sav', 'GVAS class is not a player save') in catalog.excluded


@pytest.mark.parametrize('stamp,offset', [
    (datetime.max.replace(tzinfo=timezone.utc), 2),
    (datetime.min.replace(tzinfo=timezone.utc) + timedelta(seconds=1), -2),
])
def test_extreme_date_formats_explicit_utc_without_breaking_other_cards(tmp_path, stamp, offset):
    write(tmp_path, 'HL-02-04.sav', player(stamp=stamp))
    write(tmp_path, 'HL-02-10.sav', player(stem='HL-02-10', kind='AUTO'))
    entries = browser.SaveBrowser().discover(tmp_path).entries
    displays = {e.filename: browser.format_entry(e, tz=timezone(timedelta(hours=offset))) for e in entries}
    assert displays['HL-02-04.sav'].date.endswith('UTC')
    assert displays['HL-02-10.sav'].title == 'Autosave'
