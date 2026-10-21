"""Synthetic read/preservation contracts; these do not authorize metadata writes."""

import struct

import pytest

from src.save_browser import SaveBrowser, profile_labels
from src.save_metadata import read_metadata
from tests.test_save_browser import (
    character, directory, manifest, player, prop, properties, string, structure, write,
)


@pytest.mark.parametrize('wide', [False, True])
@pytest.mark.parametrize('name', ['A', 'Élodie Example', '张𐐀 Example'])
def test_name_encoding_length_and_opaque_bytes_do_not_change_profile_identity(tmp_path, wide, name):
    raw = (name + '\0').encode('utf-16-le' if wide else 'utf-8')
    encoded = struct.pack('<i', -len(raw) // 2 if wide else len(raw)) + raw
    # Deliberately inconsistent/opaque bytes: discovery is not a name repairer.
    info = structure('CharacterSaveGameInfo', 'CharacterSaveGameInfo', properties(
        prop('CharacterID', 'IntProperty', struct.pack('<i', 1)),
        prop('CharacterName', 'StrProperty', encoded),
        prop('CurrentFormat', 'EnumProperty', string('ECharacterNameFormat::WIDE'),
             string('ECharacterNameFormat')),
        prop('CharacterNameBytes', 'ArrayProperty', struct.pack('<i', 3) + b'\xff\x80\0',
             string('ByteProperty')),
        prop('bIsUsed', 'BoolProperty', extra=b'\1'),
    ))
    first = write(tmp_path, 'HL-01-00.sav', player(
        character_info=info, stem='HL-01-00', profile=1))
    other = write(tmp_path, 'HL-03-00.sav', player(
        character_info=character(name, profile=3, wide=not wide), stem='HL-03-00', profile=3))
    index = write(tmp_path, 'SaveGameList.sav', manifest(
        directory(stem='HL-01-00', profile=1), directory(stem='HL-03-00', profile=3)))
    snapshots = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in [first, other, index]}
    service = SaveBrowser()
    for _ in range(2):
        entries = service.discover(tmp_path).entries
        assert {entry.path: (entry.slot, entry.character_name) for entry in entries} == {
            first: (1, name), other: (3, name)}
        assert profile_labels(entries) == {
            'All profiles': 'All profiles', 'Profile 1': f'Profile 1 — {name}',
            'Profile 3': f'Profile 3 — {name}'}
        assert read_metadata(first).character.profile_id == 1
    assert {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in snapshots} == snapshots


@pytest.mark.parametrize('info', [b'', structure('CharacterSaveGameInfo', 'CharacterSaveGameInfo', b'broken'),
    structure('CharacterSaveGameInfo', 'CharacterSaveGameInfo', properties(
        prop('CharacterID', 'IntProperty', struct.pack('<i', 1)),
        prop('CharacterName', 'StrProperty', struct.pack('<i', -30000)),
        prop('bIsUsed', 'BoolProperty', extra=b'\1'),
    ))])
def test_missing_or_corrupt_names_leave_index_other_profiles_and_source_bytes_untouched(tmp_path, info):
    first = write(tmp_path, 'HL-01-00.sav', player(character_info=info, stem='HL-01-00', profile=1))
    other = write(tmp_path, 'HL-03-00.sav', player(
        character_info=character('Other Person', profile=3), stem='HL-03-00', profile=3))
    index = write(tmp_path, 'SaveGameList.sav', manifest(
        directory(stem='HL-01-00', profile=1), directory(stem='HL-03-00', profile=3)))
    snapshots = {p: p.read_bytes() for p in [first, other, index]}
    entries = SaveBrowser().discover(tmp_path).entries
    assert {entry.slot: entry.character_name for entry in entries} == {1: None, 3: 'Other Person'}
    assert read_metadata(first).directory['CharacterID'] == 1
    assert {p: p.read_bytes() for p in snapshots} == snapshots
