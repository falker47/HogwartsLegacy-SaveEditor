# Nexus Mods release notes — 1.0.7

Reduced-scope compatibility and reliability update, accepted for publication by the maintainer
on 26 October 2026. Unsupported features are listed below.

## Changes

- Opens validated older, already-decompressed saves.
- Corrects Gear Offense/Defense updates to address the complete item identity and backpack slot.
  Edits are validated together and applied atomically; invalid inputs retain pending changes.
- Fixes native converter use of memory after realloc and insufficient compression-output allocation.
  The converter is rebuilt from published MIT source with pinned archive/executable hashes.
- Keeps character name fields read-only: a synchronized game-menu rename is not implemented safely yet.
- Retains the active edit session when a replacement save cannot load; cancelled uploads do nothing.
- Packages only the public asset allowlist, excluding locally acquired runtime DLLs and personal files
  from both the downloadable directory and the embedded executable.

## Supported scope and limitations

Gear stats mean the stored backpack Offense/Defense fields. Gear level, traits, appearance and
equipped totals are not exposed as newly supported edits. The separate reported Gear-slot crash
has not been reproduced and is not claimed fixed.

Merlin Trials and Butterfly chest completion are not implemented. Research readers do not establish
the reward/progression semantics needed for an Unlock All command. Generic quest skipping is unsupported.
Character renaming requires synchronized DB, metadata and index updates and remains disabled.
Game Pass export produces ordinary migration copies; it cannot write changes back to WGS or Xbox cloud saves.

Existing v1.0.6 features remain subject to their original scope; their historical in-game checks do not
certify every feature in this release. See ACCEPTANCE.md for the current tests and outstanding game acceptance.

## Use

Extract the entire package and run HogwartsLegacy-SaveEditor.exe. Work on a separate copy of your saves.
Choose the appropriate save folder, open a save, edit supported fields, click Apply, then Download Save.
The application verifies the reconstructed save before publication and retains backup safeguards.
Oodle setup is unchanged: the app automatically checks common Steam/Epic installation folders and copies the DLL when found. If it is missing, choose Yes to download it with SHA-256 verification or No to search local game libraries; manual selection is the final fallback. You do not normally need to locate the file yourself. The download fallback is a third-party GitHub source, not an official game distribution channel. The DLL is not bundled in the ZIP.

## Testing disclosure

Local native Oodle checks cover 55 exact round trips, plus 55 with forced moving allocations, and
25 real-copy Gear publications with DB1/DB2/opaque-byte comparisons. Public CI does not have Oodle.
The downloaded Windows RC was also exercised through its manager and embedded editor against an
isolated copy of a freshly created Steam save (build 20773316, game version 1613387). A glove's Offense
changed from 71 to 72; the game loaded it, displayed 72, and adjusted equipped totals by exactly 72
when equipped/removed. All six Gear categories opened without a crash. The value survived a manual
game save, complete process exit and restart/reload. The game-written DB also retained 72.

This is one profile/item, not universal gameplay certification or a reproduction of the separate
reported Gear crash. Older raw saves have file-level validation; their dedicated game round trip
remains untested. Rewards, quest skipping and synchronized rename are outside this release's scope.
