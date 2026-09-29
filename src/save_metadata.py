"""Read the tagged, uncompressed GVAS metadata without decoding database arrays.

This deliberately supports the observed UE4 GVAS v2 property layout only. Sizes
are bounds checked and opaque payloads are sought past, never decompressed.
See docs/save-browser.md for field evidence and limitations.
"""

from dataclasses import dataclass
from pathlib import Path
import struct
from typing import BinaryIO


class MetadataError(ValueError):
    """Malformed or unsupported metadata (the editor may still support the save)."""

    def __init__(self, message, player=None):
        super().__init__(message)
        self.player = player


class Reader:
    def __init__(self, stream: BinaryIO, end: int):
        self.stream = stream
        self.end = end

    def read(self, size):
        if size < 0 or size > self.end - self.stream.tell():
            raise MetadataError('Property extends beyond its container')
        value = self.stream.read(size)
        if len(value) != size:
            raise MetadataError('Truncated metadata')
        return value

    def number(self, fmt):
        return struct.unpack('<' + fmt, self.read(struct.calcsize('<' + fmt)))[0]

    def string(self):
        length = self.number('i')
        if abs(length) > 16384:
            raise MetadataError('Unreasonable FString length')
        if length == 0:
            return ''
        width = 2 if length < 0 else 1
        raw = self.read(abs(length) * width)
        if raw[-width:] != bytes(width):
            raise MetadataError('Unterminated FString')
        try:
            return raw[:-width].decode('utf-16-le' if length < 0 else 'utf-8')
        except UnicodeError as exc:
            raise MetadataError('Invalid FString encoding') from exc

    def tags(self):
        for _ in range(4096):
            name = self.string()
            if name == 'None':
                return
            kind = self.string()
            size, index = self.number('i'), self.number('i')
            subtype = None
            if kind == 'StructProperty':
                subtype = self.string()
                self.read(16)  # struct GUID
            elif kind in ('ArrayProperty', 'SetProperty', 'ByteProperty', 'EnumProperty'):
                subtype = self.string()
            elif kind == 'BoolProperty':
                subtype = self.number('B')
            elif kind == 'MapProperty':
                subtype = (self.string(), self.string())
            elif kind not in ('IntProperty', 'Int64Property', 'FloatProperty',
                              'DoubleProperty', 'StrProperty', 'NameProperty',
                              'TextProperty', 'UInt32Property', 'UInt64Property'):
                raise MetadataError(f'Unsupported property type: {kind}')
            has_guid = self.number('B')
            if has_guid not in (0, 1):
                raise MetadataError('Invalid property GUID flag')
            if has_guid:
                self.read(16)
            end = self.stream.tell() + size
            if size < 0 or end > self.end or index != 0:
                raise MetadataError('Invalid property size or array index')
            yield name, kind, subtype, Reader(self.stream, end)
            self.stream.seek(end)
        raise MetadataError('Too many properties')


@dataclass(frozen=True)
class CharacterMetadata:
    profile_id: int
    name: str


@dataclass(frozen=True)
class MetadataDocument:
    player: bool
    directory: dict | None = None
    index: dict | None = None
    character: CharacterMetadata | None = None


def _character(reader):
    profile, name, used = None, None, False
    for key, kind, subtype, value in reader.tags():
        if key == 'CharacterID' and kind == 'IntProperty':
            profile = value.number('i')
        elif key == 'CharacterName' and kind == 'StrProperty':
            name = value.string()
        elif key == 'bIsUsed' and kind == 'BoolProperty':
            used = subtype == 1
    if (used and profile is not None and profile >= 0 and name is not None
            and 0 < len(name) <= 256 and name.isprintable() and name.strip()):
        return CharacterMetadata(profile, name.strip())
    return None


def _directory(reader):
    fields = {}
    for name, kind, subtype, value in reader.tags():
        if name in ('FilenameSlot', 'CurrentMap') and kind == 'StrProperty':
            fields[name] = value.string()
        elif name == 'SaveType' and kind == 'EnumProperty' and subtype == 'ESaveType':
            fields[name] = value.string()
        elif name == 'CharacterID' and kind == 'IntProperty':
            fields[name] = value.number('i')
        elif name == 'bIsUsed' and kind == 'BoolProperty' and subtype in (0, 1):
            fields[name] = bool(subtype)
        elif name in ('SaveTime', 'GameTime') and kind == 'StructProperty' and subtype == 'DateTime':
            if value.end - value.stream.tell() != 8:
                raise MetadataError('Invalid DateTime size')
            fields[name] = value.number('q')
    return fields


def _index(reader):
    entries = {}
    valid = False
    for name, kind, subtype, value in reader.tags():
        if name == 'bIsValid' and kind == 'BoolProperty':
            valid = subtype == 1
        elif name == 'SaveFileList' and kind == 'ArrayProperty' and subtype == 'StructProperty':
            count = value.number('i')
            if count < 0 or count > 4096:
                raise MetadataError('Invalid save index count')
            if value.string() != 'SaveFileList' or value.string() != 'StructProperty':
                raise MetadataError('Unsupported save index array')
            size = value.number('q')
            if value.string() != 'SaveDirectoryEntry':
                raise MetadataError('Unsupported save index entry')
            value.read(16)
            if value.number('B') != 0 or size != value.end - value.stream.tell():
                raise MetadataError('Invalid save index array size')
            for _ in range(count):
                entry = _directory(value)
                identity = entry.get('FilenameSlot')
                if not isinstance(identity, str) or not identity or identity in entries:
                    raise MetadataError('Missing or duplicate index identity')
                entries[identity] = entry
            if value.stream.tell() != value.end:
                raise MetadataError('Unexpected data after save index')
    if not valid:
        raise MetadataError('Save index is not valid')
    return entries


def read_metadata(path: Path) -> MetadataDocument:
    """Open only in rb mode; skip compressed/uncompressed DB images by tag size."""
    with path.open('rb') as stream:
        stream.seek(0, 2)
        reader = Reader(stream, stream.tell())
        stream.seek(0)
        if reader.read(4) != b'GVAS' or reader.number('i') != 2:
            raise MetadataError('Unsupported GVAS header')
        reader.number('i')  # package version
        reader.read(10)  # UE engine major/minor/patch/changelist
        reader.string()  # engine branch
        if reader.number('i') != 3:
            raise MetadataError('Unsupported custom version format')
        count = reader.number('i')
        if count < 0 or count > 4096:
            raise MetadataError('Invalid custom version count')
        reader.read(count * 20)
        save_class = reader.string()
        player = save_class == '/Script/PersistentData.PersistentGameData'
        try:
            if player:
                character = None
                for name, kind, subtype, value in reader.tags():
                    if name == 'CharacterSaveGameInfo' and kind == 'StructProperty' and subtype == 'CharacterSaveGameInfo':
                        try:
                            character = _character(value)
                        except MetadataError:
                            # Names are optional; the enclosing tag still lets us
                            # seek to the following DirectoryEntry safely.
                            character = None
                    if name == 'DirectoryEntry' and kind == 'StructProperty' and subtype == 'SaveDirectoryEntry':
                        return MetadataDocument(player=True, directory=_directory(value), character=character)
                raise MetadataError('Missing DirectoryEntry')
            if save_class == '/Script/PersistentData.PersistentGameDataList':
                for name, kind, subtype, value in reader.tags():
                    if name == 'Info' and kind == 'StructProperty' and subtype == 'PersistentGameDataListInfo':
                        return MetadataDocument(player=False, index=_index(value))
                raise MetadataError('Missing save index Info')
            return MetadataDocument(player=False)
        except MetadataError as exc:
            # Class recognition survives a failure in optional listing metadata.
            raise MetadataError(str(exc), player=player) from exc
