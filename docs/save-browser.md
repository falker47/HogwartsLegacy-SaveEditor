# Save browser metadata

The desktop list contains player saves, with a profile selector matching the
per-character scope of the game's Load Game screen. The initial profile is the
one with the newest internal save timestamp; **All profiles** exposes every
discovered player save. Refresh preserves the chosen profile and selected path
when they are still present. Profile numbers retain the game's filename numbers.

Cards show save kind, whole hours played, location, game time, then the technical
filename. Selecting a card exposes the stored UTC timestamp, filesystem modified
time, file size, metadata source/status, and an untranslated location ID when
necessary. **Locations: English / Italiano** changes the small verified location
label catalog, independently of system locale. Unmapped locations display
**Location unavailable**; missing time is labelled **File modified**.

## Evidence and format contract

Investigation used read-only snapshots, comparing the manifest and the tagged
metadata in all available ordinary saves, spanning old uncompressed database
images and current compressed images. No save bytes, extracted databases,
personal values, or diagnostic dumps are stored in this repository.

| Field | Observed source and meaning |
| --- | --- |
| Index | `SaveGameList.sav`, GVAS v2 class `/Script/PersistentData.PersistentGameDataList`, `Info` (`PersistentGameDataListInfo`) → `SaveFileList` array of `SaveDirectoryEntry` |
| Ordinary save | GVAS v2 class `/Script/PersistentData.PersistentGameData`, top-level `DirectoryEntry` (`SaveDirectoryEntry`); this remains uncompressed after the database arrays |
| Identity | `FilenameSlot` matches the filename stem; `CharacterID` matches the profile component. Metadata identities are never used to construct a write target. Renamed player saves retain their actual path. |
| Kind | `SaveType`: `ESaveType::USER` is Manual Save; `ESaveType::AUTO` is Autosave. Observed USER slots include 00–08, with unused USER slots through 09 in the index; AUTO slots are 10–14. Other filename indices are left unknown. |
| Availability | `bIsUsed` identifies occupied index entries. Unused or missing entries never suppress existing player saves; their own metadata is used and marked `not indexed`. |
| Timestamp | `SaveTime`, `DateTime` struct containing signed little-endian 64-bit ticks. The stored value is UTC in the observed saves, corroborated against new file times and Load Game. |
| Playtime | `GameTime`, also serialized as `DateTime` ticks, holds elapsed duration rather than a calendar date. Dividing by 10,000,000 gives seconds, and whole hours agree with Load Game. The ordinary save's `SessionTime` corroborates this value. |
| Location | `CurrentMap` is a localization key, not display-ready text. No display label table was found in the index, ordinary save metadata, embedded dynamic database schema, or existing repository resources. |

The tick unit and epoch are documented by
[Epic's FDateTime API](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Core/Misc/FDateTime?application_version=5.5):
100 ns since January 1, year 1. Game-specific UTC/duration semantics above come
from local comparison, not the type name alone.

The index is authoritative when it agrees with the ordinary save. It stores
fixed profile/slot order, **not chronological menu order**. The browser sorts by
verified `SaveTime` descending within the selected profile, then filename for
ties. Metadata-less saves follow, sorted by filesystem mtime descending and
filename for ties. Filename indices and mtimes are not game chronology.

The observed Load Game screen renders historical winter saves using the current
summer UTC offset. Cards therefore use the current fixed local UTC offset for
all game timestamps. The info panel names that offset and shows the canonical
UTC value separately. This is an observed UI convention, not a claim about the
game's code or every game/platform version.

The four verified location mappings are:

| CurrentMap | English | Italiano |
| --- | --- | --- |
| `Overland` | The Highlands | Le Highlands |
| `RegionNameHelmsdale` | Cragcroftshire | Cragcroftshire |
| `Hamlet_Aranshire` | Aranshire | Aranshire |
| `RegionNameSouthCoast` | Clagmar Coast | Clagmar Coast |

The Load Game observations establish these pairs; the localization key identities
are independently corroborated by the corresponding entries in the
[community localization source](https://github.com/Markismus/Hogwarts-Legacy-Dutch-text/blob/main/MAIN-nlNL.json).
That project's translated prose is not bundled. New mappings require comparable
evidence; identifiers are never prettified into invented labels. Game installation
resources are packaged separately; the browser neither extracts nor distributes
those assets and does not require a game install to list saves.

An apparent newer filesystem autosave missing from the reference Load Game image
was resolved by the capture sequence: the game image preceded the newer autosave,
and the manager image followed it. Both autosaves are marked used in the index
and agree with their own metadata; neither is hidden or transient based on this
evidence.

## Read-only discovery and fallbacks

`SaveGameList.sav` and `SavedUserOptions.sav` are support files and never appear as
editable saves. Other non-player GVAS classes and unrecognized files are excluded.
Canonical `HL-<profile>-<slot>.sav` files remain selectable on metadata failure;
renamed files are recognized by their player GVAS class.

`hlsaves -d` cannot decode the index: it reports a missing `RawDatabaseImage`.
It successfully decompresses ordinary saves, but discovery does not invoke it.
The bounded reader follows property sizes and seeks over compressed or uncompressed
database arrays. It reads only headers and the needed uncompressed fields, with
limits on strings, property counts, array counts, and enclosing stream lengths.
Unsupported layouts fail locally instead of scanning for arbitrary byte markers.

A single background worker owns the metadata cache. Tk widgets are created and
updated only by main-thread polling; outdated folder/refresh results are ignored.
Cache keys include path, size, nanosecond mtime and ctime. Changed/deleted files and
changed indexes are reconsidered; unchanged refreshes reuse parsed metadata.
Failures are logged and cached too. A stale index that disagrees with the file
uses the file's own `DirectoryEntry`, with a visible status. Absent, malformed or
partial metadata never fabricates playtime, a location, or game time.

Browsing does not create a backup directory or otherwise write into the save
folder. Backups are still created immediately before editing, in the same
`Backups` directory with the same naming and contents as before. The edit worker
captures the selected source path before starting; subsequent card selection or
refresh cannot retarget its backup, decompression input, or editor write-back.
The compression pipeline and embedded editor's database mutations are unchanged.

## Verification

`python -m pytest tests -q` covers generated metadata fixtures, exclusions,
manual/autosave classification, index and file agreement, malformed input,
ordering, cache invalidation, display fallbacks, profile selection, stale worker
results and exact source paths. No fixture contains a real database or gameplay
data. Run `npm test` and `npm run build` in `HLSE-src` for the embedded editor's
existing recovery regression suite and production build.
