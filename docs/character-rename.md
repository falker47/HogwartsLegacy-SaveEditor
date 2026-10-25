# Character rename investigation — 21 October 2026

Base: live `main` at `6a1fc9cd901cdb45a91a300e29a71cb00a35ad90`.
Branch: `codex/fix-character-menu-rename`.

## Delivered scope

This is a safety mitigation, **not a completed synchronized rename**. Player's
First Name and Last Name are read-only. `modifyPlayerData` rejects actual name
changes during validation, before its transaction or any UPDATE, including mixed
name/resource/progression patches. The legacy `modifyPlayerName` entry point now
uses the same owner-scoped validation instead of two unscoped UPDATEs. Unchanged
names remain acceptable in full-form calls. Other supported Player edits continue.
The warning states that existing mismatches are not repaired.

No GVAS writer, manifest writer, profile-wide rewrite or automatic repair is added.
The user explicitly required no speculative write-back when safety cannot be
proved. The remaining format and gameplay gates below are not established by
synthetic tests or a successful compression round trip.

Custom DB Upload deliberately replaces supplied DB1/DB2 bytes through the existing
lower-level workflow. It is outside the Player guard and can still import database
names inconsistent with metadata. It is **not a supported rename workflow**. Raw
SQLite export is also unchanged and makes no menu-synchronization claim.

## Reproduction and data flow

1. Player reads `MiscDataDynamic` rows owned by `Player`, named `PlayerFirstName`
   and `PlayerLastName`. Before this mitigation, Apply changed those rows only.
2. `SaveGameManager.generateSaveFile` exports DB1 and passes it to `SaveGameData`.
   That generator replaces DB arrays and preserves the remaining GVAS tail.
3. The ordinary save's `CharacterSaveGameInfo.CharacterName` is in that tail.
   The old name and `CharacterNameBytes` therefore survive a DB-only rename.
4. Neither frontend generation nor Python `EditorApi` updates `SaveGameList.sav`.
   Its separate character copies can retain the old name too.
5. The desktop browser intentionally labels profiles from ordinary-save metadata;
   changing that label to query DB1 would hide the discrepancy, not repair the game.

The regression tests reproduce this with tagged synthetic containers and real
sql.js exports, covering short/long and UTF-8/UTF-16 names. Direct DB replacement
models the former behavior explicitly; it is not an enabled rename API.

## Authorized real-copy evidence

The user explicitly authorized the displayed Profile 1 save sequence as
sacrificial. Eleven `HL-01-*.sav` files and `SaveGameList.sav` were copied into an
ignored, unique worktree temporary directory and compared byte-for-byte. Only
those additional copies entered native conversion. No game-directory file was
replaced. No save bytes, extracted databases, personal names, UIDs, account path or
DLL are committed, uploaded or included as fixtures. Other profiles were not edited.

Read-only tagged traversal found:

| Field | Observation | Write implication |
| --- | --- | --- |
| Ordinary `CharacterName` | A positive-length FString in each of the 11 inspected saves | A writer would have to update both FString and enclosing property sizes for length changes. |
| `CurrentFormat` | `ECharacterNameFormat::WIDE` in all 11 copies | The enum name alone does not prove the byte-array encoding. |
| `CharacterNameBytes` | Count agrees with payload size; observed ASCII name bytes plus one NUL agree with `CharacterName` | These ASCII samples also match UTF-8. They do not distinguish UTF-8 from other ASCII-compatible encodings or prove non-ASCII/WIDE write rules. They do not match UTF-16LE plus a two-byte NUL. |
| Index `Info.CharacterList` | Five tagged character structs, including unused entries; names are shared by multiple used profiles | Match technical identity, never name text or array position alone. |
| `LastLoadedCharacter` | Explicit ID and UID match Profile 1 | A single cached character does not represent every profile. |
| `CurrentCharacter` | No serialized `CharacterID`; UID uniquely matches Profile 1 in this copy | Missing ID must not be invented; a future writer needs verified UID-aware matching and ambiguity rejection. |
| Other identity/progression | CharacterUID, directory identity, appearance/state and gameplay data also coexist with names | None of these are authorized rename targets. |

On a further copy of the newest authorized save:

- Pinned vendored hlsavetool and the existing local Oodle DLL decompressed and
  recompressed the file; decompression of the candidate equaled the initial
  decompressed bytes exactly. DB1 and DB2 each passed SQLite `integrity_check`.
- The original DB1 first/last name joined with a space matched GVAS `CharacterName`.
- A controlled DB-only rename to synthetic values through the production container
  generator reproduced stale GVAS `CharacterName`; `DirectoryEntry` stayed equal.
  Native compression/decompression of that probe was byte-exact too. This proves
  the converter's round trip alone cannot detect the semantic discrepancy.
- The production `modifyPlayerData` and legacy `modifyPlayerName` guards rejected
  attempted synthetic names against the real DB1; exports before and after were
  byte-identical. No candidate was published into the game directory.

The native converter initially could not load its DLL when the DLL was outside
its executable directory. An isolated temporary runtime containing the pinned
executable and the existing DLL resolved that setup issue. No DLL was downloaded
or placed under packaged assets.

## Integrity and failure behavior

Rename requests fail before mutation, so this change does not create a transaction
spanning several save files. Missing/ambiguous DB name rows still fail existing
validation. Missing/corrupt optional menu metadata cannot authorize a rename.
No profile is selected or retargeted using a display name.

The existing desktop pipeline continues to verify an exclusive backup before
editing, pin the selected source snapshot, stage conversion beside its destination,
require an exact decompression round trip, recheck the source digest and publish
one file with `os.replace`. Its prior failure/backup limitations remain documented
in [the integrity audit](save-integrity-audit.md). No second file is added to that
single-file publication contract. Game Pass/WGS containers are never write targets.

Tests additionally snapshot index, another save and another profile during normal
and custom full-save downloads, for both bridge variants, across success/failure.
Existing fault injection continues to cover backup, short writes, disk-full,
permissions, stale source, converter errors, interruption and atomic publication.

## Verification and remaining gates

Automated coverage includes changed/unchanged names, both entry points, mixed-patch
atomic rejection, page error/reset behavior, rendered read-only fields, different
name lengths, non-ASCII UTF-8 and UTF-16 surrogate pairs, missing/corrupt optional
metadata, duplicate display names with distinct profile IDs, exact opaque-tail/DB2
preservation, and unaffected-file snapshots. Python name fixtures remain generated
metadata only and explicitly preserve opaque `CharacterNameBytes`.

Exact final local suite/build results and remote PR checks are recorded in the
handoff. Native real-copy results above are scoped to those copies; no in-game
acceptance or universal save-format compatibility is claimed.

A complete rename remains gated on:

1. Observing non-ASCII name serialization and `CurrentFormat` transitions in
   sacrificial saves generated by the game, including UTF-8/UTF-16 cases.
2. Establishing which ordinary/index copies the game reads and regenerates, and
   whether historical saves should retain their historical names. Verify
   CharacterList, LastLoadedCharacter and UID-matched CurrentCharacter separately.
3. Implementing only the proven field updates with strict bounds, sizes, identity,
   duplicate/missing/corrupt metadata validation and preservation of all other bytes.
4. Defining a recoverable, verified-backup transaction for every affected file,
   rejecting concurrent changes and proving recovery from failure between writes
   or hard termination. Several `os.replace` calls are not one atomic transaction.
5. Confirming character-selection menu, load, save, reload, progression, other
   characters and historical slots on disposable copies. No game process/menu
   was available to the current automated session.

Until those gates pass, keep renaming unavailable and do not publish a release or
claim the character-selection bug has been fully fixed.


## Follow-up: public schema and game availability

The continuation checked the installed Windows Computer Use runtime successfully;
UI observation is available if a game window can be opened. No Hogwarts Legacy
app/window, Steam library entry, Epic installation manifest, registered uninstall
entry or installation in the inspected common gaming directories was found.
This is a bounded availability check, not proof that the game is absent everywhere.
The additional path supplied by the user contains `HogwartsLegacy-SaveEditor.exe`
and editor assets, not `HogwartsLegacy.exe`. The game's actual path remains needed.
No unrelated running app was activated and no game or profile was changed.

Public primary schema sources were also checked at immutable revisions:

- [PhoenixUProj CharacterSaveGameInfo.h](https://github.com/narknon/PhoenixUProj/blob/6decac117d27bb4817913d306a5c417f82675d74/Source/PersistentData/Public/CharacterSaveGameInfo.h)
  declares FString CharacterName separately from CurrentFormat and the uint8
  CharacterNameBytes array; the latter two carry SaveGame reflection flags.
- [Roadou PersistentData_struct.h](https://github.com/Roadou/HogwartsLegacy-SDK/blob/12ffa8a46fb84e7ed13a528715dfd8bb5521594c/src/PersistentData_struct.h)
  independently exposes NONE/ANSI/WIDE enum values and the same character/index
  field family. These are reflected memory layouts, not serialized write rules.
- [PhoenixUProj PersistentData.cpp](https://github.com/narknon/PhoenixUProj/blob/6decac117d27bb4817913d306a5c417f82675d74/Source/PersistentData/Private/PersistentData.cpp)
  contains a stub for UpdatePlayableCharacterName that simply returns false,
  along with other empty/default-return implementations. It does not reveal the
  game's name encoding, which file copies are updated, or recovery semantics.

These sources corroborate why writing only CharacterName is not justified. They
cannot replace game-generated non-ASCII fixtures or menu/load/save observations.
No new runtime, game, mod, plugin or service was installed to obtain this evidence.

## Revalidation — 25 October 2026

The live base is still main 6a1fc9cd901cdb45a91a300e29a71cb00a35ad90; PR #21 remained Draft at 26f93529f029cdc4e6dc2087a1535f3d7929e067 before this documentation update. Its exact-head CI run [39676128471](https://github.com/falker47/HogwartsLegacy-SaveEditor/actions/runs/39676128471) succeeded. Fresh local verification passed 195 Python tests (Python 3.14) and 73 frontend tests; no product code is changed by this update.

The user broadened authorization to all available saves for sacrificial testing. We created and verified independent copies of 25 ordinary saves plus two support files. Analysis and native transformations used only these additional copies under ignored temporary storage. All 27 original source hashes were verified unchanged afterward; config.json was not read. Both SQLite images in all 25 saves passed integrity_check. Four inputs were already-uncompressed older GVAS, explaining why the converter returns success without producing a decompressed destination; that independent compatibility issue is handled on a separate branch.

All 25 observed CharacterName values remain positive-length ASCII FStrings with CurrentFormat=WIDE; CharacterNameBytes matches the ASCII/UTF-8 bytes plus NUL in those observations. This still does not distinguish non-ASCII encodings or prove a writable WIDE/ANSI transition. It adds no basis to enable rename or to synchronize index/historical copies automatically. No name, UID, account path, save, extracted database or DLL is committed.

The historical availability blocker changed: a Steam install is now present (manifest state 4, build 20773316). There was no active game process. No demonstrated save-path isolation mechanism was established, so the game was not launched against the original directories; menu/load/save/reload and game-generated non-ASCII experiments remain NOT_EXECUTED / HUMAN_GATE. Generic Unreal command-line documentation is not proof that this particular game build redirects every save/index/cloud path safely. No unverified flag or original-folder replacement is used.

The precise remaining prerequisite is an isolated game test session with disposable fixtures: establish non-ASCII serialization and actual metadata consumers first, then implement a recoverable multi-file transaction only if those observations justify it. The read-only UI/backend rename guard and Draft status remain in place; the full synchronized-rename objective remains PARTIAL.
