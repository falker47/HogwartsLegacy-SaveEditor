# Save browser metadata

The desktop list contains player saves, with a profile selector matching the
per-character scope of the game's Load Game screen. The initial profile is the
one with the newest internal save timestamp; **All profiles** exposes every
discovered player save. Refresh preserves the chosen profile and selected path
when they are still present. Profile numbers retain the game's filename numbers.
Choices include the character name when available (`Profile N — <name>`).
The selection key remains `Profile N`, so duplicate names and later name changes
cannot change the selected profile or source path. A missing name leaves `Profile N`.

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

The six verified location mappings are:

| CurrentMap | English | Italiano |
| --- | --- | --- |
| `Overland` | The Highlands | Le Highlands |
| `RegionNameHelmsdale` | Cragcroftshire | Cragcroftshire |
| `Hamlet_Aranshire` | Aranshire | Aranshire |
| `RegionNameSouthCoast` | Clagmar Coast | Clagmar Coast |
| `RegionNameHogwartsArea` | North Hogwarts Region | Regione Nord di Hogwarts |
| `CombatChallenge_DigitalDeluxe_HN_AU` | Dark Arts Battle Arena | Arena di combattimento delle Arti Oscure |

The Load Game observations establish these pairs; the localization key identities
are independently corroborated by the corresponding entries in the
[community localization source](https://github.com/Markismus/Hogwarts-Legacy-Dutch-text/blob/main/MAIN-nlNL.json).
That project's translated prose is not bundled. New mappings require comparable
evidence; identifiers are never prettified into invented labels. Game installation
resources are packaged separately; the browser neither extracts nor distributes
those assets and does not require a game install to list saves.

The additional Profile 3 comparison on 2026-09-29 established the last two
Italian labels exactly. Read-only parsing found `RegionNameHogwartsArea` in
`HL-03-00.sav`, and `CombatChallenge_DigitalDeluxe_HN_AU` in `HL-03-11.sav`,
`HL-03-10.sav`, `HL-03-14.sav`, `HL-03-13.sav`, and `HL-03-12.sav`. Each agrees
with its used manifest entry. The English region label is corroborated by the
[Gamer Guides region entry](https://www.gamerguides.com/hogwarts-legacy/database/locations/regions/north-hogwarts-region);
the arena label is corroborated by the publisher's
[Dark Arts Pack listing](https://store.steampowered.com/app/1880832?l=english).
The community localization source also contains both exact keys; its Dutch
translations are not used as evidence of English wording.

The manual comparison now passes profile separation, save type, whole hours,
timestamps and ordering. The six Profile 3 entries format at the observed
current UTC+02:00 offset as 27 Jan 2026, 19:37 (manual, North Hogwarts Region),
then 19:35, 19:31, 19:27, 19:22 and 19:16 (autosaves, Dark Arts Battle Arena).
All six show 46h. Other unknown IDs still use the explicit unavailable label.

## Character-name evidence and selection

The format inspection enumerated tagged fields instead of searching database
bytes or assuming a name property. Both sources contain an uncompressed
`CharacterSaveGameInfo` struct:

- Ordinary saves: top-level `CharacterSaveGameInfo`, after the database/minimap
  arrays and before `DirectoryEntry` in the observed layout.
- `SaveGameList.sav`: `Info.CharacterList`, a struct array keyed by each entry's
  `CharacterID`. `LastLoadedCharacter` and `CurrentCharacter` also exist, but
  describe a single character and are not suitable for labeling every profile.

In all 25 local player saves, the `CharacterName` FString, `CharacterID` and
`bIsUsed` agree with the corresponding used manifest character. The observed
`CharacterNameBytes` also corroborates the name; the reader does not need to
interpret that redundant array or `CurrentFormat`. No personal name values are
stored in this document or the synthetic tests. The active local profiles have
the same name, so the technical IDs remain essential for distinguishing them.

The implementation reads only the ordinary save's `CharacterID`, `CharacterName`
and `bIsUsed` using the existing bounded reader, then caches them with the other
metadata. It requires a used entry, matching character/directory/profile IDs,
and a nonblank printable name of at most 256 characters. UTF-8 and UTF-16
FStrings are supported. Invalid optional name metadata is skipped without
discarding a valid `DirectoryEntry`. The newest usable name in each profile's
ordered saves labels its choice, independently of the manifest's location/time
precedence. Names are deliberately not recovered from a manifest alone when
the ordinary file's character identity cannot be verified.

This adds no database decompression, database queries, subprocesses, extra file
opens or persistent personal-data cache. `MiscDataDynamic` contains
`PlayerFirstName` / `PlayerLastName` used by the embedded editor, but that heavier
path is unnecessary for browser labels. An editor that changes only database
names may leave the menu metadata stale; the browser shows the saved menu name.

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
