"""Recognize validated, already-uncompressed GVAS without rewriting its bytes."""
from contextlib import closing
from io import BytesIO
import sqlite3

from .save_metadata import MetadataError, Reader


def is_uncompressed_save(data: bytes) -> bool:
    """Accept tagged raw SQLite arrays, never a signature scan or converter text.

    This is a read-only compatibility check for observed GVAS v2 saves. Unknown,
    compressed, malformed, or corrupt data stays on the existing converter path.
    SQLite is checked entirely in memory. Both image tags are required by the
    embedded editor; DB2 may be an empty array.
    """
    stream = BytesIO(data)
    reader = Reader(stream, len(data))
    try:
        if reader.read(4) != b'GVAS' or reader.number('i') != 2:
            return False
        reader.number('i')  # package version
        reader.read(10)  # engine version and changelist
        reader.string()
        if reader.number('i') != 3:
            return False
        count = reader.number('i')
        if count < 0 or count > 4096:
            return False
        reader.read(count * 20)
        if reader.string() != '/Script/PersistentData.PersistentGameData':
            return False
        images = set()
        primary_end = None
        for name, kind, subtype, value in reader.tags():
            if name in ('RawDatabaseImage', 'RawExclusiveImage'):
                if name in images or kind != 'ArrayProperty' or subtype != 'ByteProperty':
                    return False
                images.add(name)
                count_offset = stream.tell()
                marker_offset = data.find(name.encode('ascii'))
                byte_header = data.find(b'ByteProperty', marker_offset) if marker_offset >= 0 else -1
                # The embedded writer still locates arrays with a byte scanner
                # and fixed size offsets. Do not newly admit tagged layouts
                # (GUIDs, reversed arrays, decoys) it cannot preserve exactly.
                if (byte_header < 0 or byte_header + len(b'ByteProperty') + 2 != count_offset
                        or data[count_offset - 1] != 0
                        or name == 'RawExclusiveImage' and (primary_end is None or count_offset < primary_end)):
                    return False
                length = value.number('i')
                if int.from_bytes(data[count_offset - 26:count_offset - 22], 'little', signed=True) != length + 4:
                    return False
                if name == 'RawDatabaseImage':
                    primary_end = value.end
                if length < 0 or length != value.end - stream.tell():
                    return False
                if length == 0:
                    if name == 'RawDatabaseImage':
                        return False
                else:
                    payload = value.read(length)
                    if not payload.startswith(b'SQLite format 3\0'):
                        return False
                    # SQLite integrity_check alone ignores bytes beyond the
                    # header's page count. Require an exact standalone image.
                    if len(payload) < 100:
                        return False
                    page_size = int.from_bytes(payload[16:18], 'big')
                    page_size = 65536 if page_size == 1 else page_size
                    pages = int.from_bytes(payload[28:32], 'big')
                    if (page_size < 512 or page_size > 65536
                            or page_size & (page_size - 1)
                            or pages == 0 or pages * page_size != length):
                        return False
                    with closing(sqlite3.connect(':memory:')) as db:
                        db.deserialize(payload)
                        if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                            return False
        return images == {'RawDatabaseImage', 'RawExclusiveImage'}
    except (MetadataError, sqlite3.Error, ValueError, OverflowError):
        return False
