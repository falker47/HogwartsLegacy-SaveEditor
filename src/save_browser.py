"""Read-only save catalog, metadata cache, semantic ordering and presentation."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, tzinfo
import logging
from pathlib import Path
import re

from .save_metadata import MetadataDocument, MetadataError, read_metadata
from .utils import format_file_size


LOGGER = logging.getLogger(__name__)
PLAYER_NAME = re.compile(r'HL-(\d+)-(\d+)\.sav', re.IGNORECASE)
SYSTEM_NAMES = {'savegamelist.sav', 'saveduseroptions.sav'}
EPOCH = datetime(1, 1, 1, tzinfo=timezone.utc)

# Only labels corroborated by Load Game observations; see docs/save-browser.md.
# Unknown keys remain explicitly unavailable, rather than guessed title casing.
LOCATION_LABELS = {
    'en': {'Overland': 'The Highlands', 'RegionNameHelmsdale': 'Cragcroftshire',
           'Hamlet_Aranshire': 'Aranshire', 'RegionNameSouthCoast': 'Clagmar Coast'},
    'it': {'Overland': 'Le Highlands', 'RegionNameHelmsdale': 'Cragcroftshire',
           'Hamlet_Aranshire': 'Aranshire', 'RegionNameSouthCoast': 'Clagmar Coast'},
}


@dataclass(frozen=True)
class SaveEntry:
    path: Path
    editable: bool
    save_kind: str
    slot: int | None
    autosave_index: int | None
    internal_timestamp: datetime | None
    playtime_seconds: float | None
    location_id: str | None
    filesystem_mtime: float
    size: int
    metadata_source: str
    metadata_status: str

    @property
    def filename(self):
        return self.path.name


@dataclass(frozen=True)
class SaveCatalog:
    entries: tuple[SaveEntry, ...]
    excluded: tuple[tuple[str, str], ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class SaveDisplay:
    title: str
    summary: str
    date: str
    technical: str
    details: str


def _timestamp(ticks):
    if type(ticks) is not int or ticks <= 0:
        return None
    try:
        return EPOCH + timedelta(microseconds=ticks // 10)
    except OverflowError:
        return None


def _entry(path, stat, metadata, source, status):
    match = PLAYER_NAME.fullmatch(path.name)
    slot, index = (int(match[1]), int(match[2])) if match else (None, None)
    # Verified USER slots 00..09 and AUTO slots 10..14. Do not infer unknown slots.
    kind = 'manual' if index is not None and index <= 9 else 'auto' if index is not None and 10 <= index <= 14 else 'unknown'
    kind = {'ESaveType::USER': 'manual', 'ESaveType::AUTO': 'auto'}.get(metadata.get('SaveType'), kind)
    character = metadata.get('CharacterID')
    if slot is None and type(character) is int and character >= 0:
        slot = character
    stamp = _timestamp(metadata.get('SaveTime'))
    game_ticks = metadata.get('GameTime')
    playtime = game_ticks / 10_000_000 if type(game_ticks) is int and game_ticks >= 0 else None
    location = metadata.get('CurrentMap') or None
    if status == 'complete' and (stamp is None or playtime is None or location is None or kind == 'unknown'):
        status = 'partial'
    return SaveEntry(path, True, kind, slot, index if kind == 'auto' else None,
                     stamp, playtime, location, stat.st_mtime, stat.st_size, source, status)


def sort_entries(entries):
    """Metadata-bearing saves first; deterministic filesystem fallback at the end."""
    return sorted(entries, key=lambda e: (
        e.internal_timestamp is None,
        -(e.internal_timestamp.timestamp() if e.internal_timestamp else e.filesystem_mtime),
        e.filename.casefold(), e.filename, str(e.path),
    ))


class SaveBrowser:
    """Used by one worker. Cache failures too; replace entries on stat changes."""

    def __init__(self):
        self._cache = {}

    def _read(self, path, stat):
        key = (str(path), stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
        cached = self._cache.get(path)
        if cached and cached[0] == key:
            return cached[1:]
        document, error = None, None
        try:
            document = read_metadata(path)
            after = path.stat()
            if (after.st_size, after.st_mtime_ns, after.st_ctime_ns) != key[1:]:
                raise MetadataError('File changed while metadata was being read; refresh again')
        except (OSError, ValueError, OverflowError) as exc:
            document, error = None, str(exc)
            if isinstance(exc, MetadataError) and exc.player is not None:
                document = MetadataDocument(player=exc.player)
            LOGGER.warning('Save metadata unavailable for %s: %s', path.name, exc)
        self._cache[path] = (key, document, error)
        return document, error

    def discover(self, directory: Path) -> SaveCatalog:
        paths = sorted((p for p in directory.iterdir() if p.suffix.lower() == '.sav' and p.is_file()),
                       key=lambda p: (p.name.casefold(), p.name))
        entries, excluded, warnings = [], [], []
        index = {}
        manifest = next((p for p in paths if p.name.lower() == 'savegamelist.sav'), None)
        if manifest:
            try:
                document, error = self._read(manifest, manifest.stat())
                if error:
                    warnings.append(f'{manifest.name}: {error}')
                if document and document.index is not None:
                    index = document.index
            except OSError as exc:
                warnings.append(f'{manifest.name}: {exc}')
        for path in paths:
            if path.name.lower() in SYSTEM_NAMES:
                excluded.append((path.name, 'System/support save'))
                continue
            try:
                stat = path.stat()
            except OSError as exc:
                warnings.append(f'{path.name}: {exc}')
                continue
            document, error = self._read(path, stat)
            if document and not document.player:
                excluded.append((path.name, 'GVAS class is not a player save'))
                continue
            if not document and not PLAYER_NAME.fullmatch(path.name):
                excluded.append((path.name, 'Unrecognized player save'))
                continue
            if error:
                warnings.append(f'{path.name}: {error}')
            own = document.directory if document and document.directory else {}
            listed = index.get(path.stem, {})
            source, status, metadata = 'filename/filesystem', 'fallback', {}
            if own:
                source, status, metadata = 'DirectoryEntry', 'complete', own
            if listed.get('bIsUsed') is True:
                fields = ('FilenameSlot', 'CharacterID', 'SaveType', 'SaveTime', 'GameTime', 'CurrentMap')
                if own and any(own.get(field) != listed.get(field) for field in fields):
                    status = 'index mismatch'
                    warnings.append(f'{path.name}: index differs; using this file\'s DirectoryEntry')
                else:
                    source, status, metadata = 'SaveGameList.sav', 'complete', listed
                    if error:
                        status = 'file metadata unavailable'
            elif own and manifest:
                status = 'not indexed'
            entries.append(_entry(path, stat, metadata, source, status))
        self._cache = {p: v for p, v in self._cache.items() if p in paths}
        return SaveCatalog(tuple(sort_entries(entries)), tuple(excluded), tuple(warnings))


def _display_date(value, tz):
    try:
        return value.astimezone(tz).strftime('%d %b %Y, %H:%M')
    except (OverflowError, ValueError):
        # UTC is still meaningful when applying the offset would overflow.
        return value.strftime('%d %b %Y, %H:%M UTC')


def format_entry(entry: SaveEntry, locale='en', tz: tzinfo | None = None) -> SaveDisplay:
    # The observed game menu applies the CURRENT UTC offset to historical saves.
    # A fixed-offset tz preserves that behavior across DST boundaries.
    tz = tz or datetime.now().astimezone().tzinfo
    title = {'auto': 'Autosave', 'manual': 'Manual Save'}.get(entry.save_kind, 'Player Save')
    labels = LOCATION_LABELS.get(locale, LOCATION_LABELS['en'])
    location = labels.get(entry.location_id, 'Location unavailable')
    playtime = f'{int(entry.playtime_seconds // 3600)}h' if entry.playtime_seconds is not None else 'Playtime unavailable'
    try:
        file_date = _display_date(datetime.fromtimestamp(entry.filesystem_mtime, timezone.utc), tz)
    except (OSError, OverflowError, ValueError):
        file_date = 'Unavailable'
    date = (_display_date(entry.internal_timestamp, tz)
            if entry.internal_timestamp else 'File modified: ' + file_date)
    profile = f'Profile {entry.slot}' if entry.slot is not None else 'Profile unknown'
    technical = f'{entry.filename} · {profile}'
    utc = entry.internal_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') if entry.internal_timestamp else 'Unavailable'
    offset = datetime.now(tz).strftime('%z')
    details = (f'{entry.filename}\n{title} · {profile}\n{playtime} | {location}\n'
               f'Game time: {date if entry.internal_timestamp else "Unavailable"}\n'
               f'Display offset: UTC{offset[:3]}:{offset[3:]} (current)\n'
               f'Stored time: {utc}\n'
               f'Filesystem modified: {file_date}\n'
               f'Size: {format_file_size(entry.size)}\n'
               f'Metadata: {entry.metadata_source} ({entry.metadata_status})')
    if entry.location_id and location == 'Location unavailable':
        details += f'\nLocation ID: {entry.location_id}'
    return SaveDisplay(title, f'{playtime} | {location}', date, technical, details)
