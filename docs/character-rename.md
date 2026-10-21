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
