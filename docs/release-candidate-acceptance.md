# 1.0.7-rc1 acceptance — 26 October 2026

**Release readiness: NOT_READY for the complete requested Nexus scope.** A concrete reduced-scope
Windows candidate is being delivered through the existing Draft PR #26. No main merge, public release,
Nexus upload or archive-PR #27 integration is authorized or performed. The artifact's QA-MANIFEST.json
records its exact source commit, file sizes and SHA256 hashes.

## Evidence and user requests

Sources checked live: [Nexus posts](https://www.nexusmods.com/hogwartslegacy/mods/2414?tab=posts),
[Nexus bugs](https://www.nexusmods.com/hogwartslegacy/mods/2414?tab=bugs),
[GitHub issue 3](https://github.com/falker47/HogwartsLegacy-SaveEditor/issues/3),
[GitHub issue 2](https://github.com/falker47/HogwartsLegacy-SaveEditor/issues/2), repository audit documents.
The live posts page exposed ten discussions; older items below are also grounded in the repository's
dated audits. Pagination retrieval was unavailable, so this is not an assertion that all 120 comments
were reread. Positive author replies and historical green tests are not fresh acceptance evidence.

| Request / source | Implementation | Actual verification | Outcome / remaining limit |
|---|---|---|---|
| Character-selection rename, Boughten, 4 Oct | PR21 guard integrated; name UI and backend reject partial rename | Frontend metadata-preservation/blocked-write tests | PARTIAL: mitigation only. No multi-file writer; Unicode, index consumers and recovery semantics unproven |
| Gear stat editing, cerealkiller667, 15 Oct | PR23 composite GearID+GearVariation+slot targeting; stat-only atomic batches | Real manager/generator/publication on 25 copied saves, including duplicate variation; compare every DB1 table/field, DB2 and opaque bytes | FILE-LEVEL PASS; equip/unequip, totals and game persistence pending |
| Gear-slot crash, arftrolizia, 22 Oct | No speculative patch attributed to this report | Gear frontend tests and copy edits pass; no reporter fixture/reproduction | NOT_REPRODUCED; not claimed fixed |
| Complete Merlin/Butterflies, slmenzies, 14 Oct | PR24 read-only anonymous probe integrated | Probe schema/catalog tests; no writer | NOT_IMPLEMENTED. Requires controlled solve/reward/collection/save/reload transitions in both DBs |
| Already-decompressed saves, PR22 real-copy finding | Validated raw staging without converter output assumption | Four older raw saves among 25 real-copy cases; raw-layout and malformed-layout tests | FILE-LEVEL PASS for verified layout; unsupported layouts rejected |
| Native converter failure, PR25 QA reproduction | HL-02C realloc-source and HL-02D checked output growth promoted with HL-02A | Real Oodle: 11 synthetic cases x5 cycles, repeated with forced-moving allocation; source/DB1/DB2/tail exact | PASS on tested corpus; no universal malformed-save or gameplay certification |
| Game Pass detection / edits revert, michaelcarra97, 14 Oct; earlier detection report | Existing WGS detection and copy export preserved | WGS refusal/export/browser regression suites | EXPORT ONLY; WGS container/cloud write-back unsupported |
| No saves found, Nexus bug list | Existing browser, manual folder override and auto-detect preserved | Discovery/path/browser tests, copied saves | Generic report lacks reproducible details; not closed as fixed |
| First page does not work, Nexus bug list | Reproduced separate cancelled/invalid-upload defect; fixed empty selection and atomic session replacement with visible error | New regressions fail before fix, pass after; both bridge variants | Concrete upload bug fixed; no assertion it is the original vague Nexus report |
| DB1/DB2 download error, GitHub #3 / Nexus bug | Existing raw export path preserved | Real Python API + JS bridge regression suite, raw-byte/hash/SQLite and no write-back checks | AUTOMATED PASS; historically fixed in 1.0.6 |
| Raw database attributes, GitHub #2 | Existing export/external SQL/custom upload workflow | Existing custom-save and raw-export tests | PARTIAL; no integrated arbitrary-SQL editor added |
| XP/Talent prerequisite failure, JwontTellU34276 / Jakepaul5 | Existing bounded progression and learned+unspent <=36 validation preserved | Existing owner/dirty-write/validation regressions | Existing feature; no prerequisite bypass or damaged-save repair claimed |
| Revelio pages, tntltct01, 3 Jul; Wand Handles, historical audit | Existing v1.0.6 implementation retained | Existing frontend regressions | Historical game acceptance only; not newly certified by this candidate |
| Skip broken quest, SKEEZo24, 8 Jun | None | No verified state transition | NOT_IMPLEMENTED; no generic quest writer |

## Reproducible checks

- Windows is available. Hogwarts Legacy Steam build 20773316 is installed. Original VS2019 compiler
  is not available; existing MSYS2 UCRT64 GCC 13.1.0 compiles the promoted runtime. Actions also compiles
  the patched source with MSVC. No speculative compiler installation was performed.
- User confirmed the existing local Oodle DLL's legitimate origin. It is used only locally and never bundled.
- `scripts/validate_native_roundtrip.py --converter <exe> --expected-sha256 <hash> --out-dir <new-directory>`:
  55 byte-exact cycles; valid SQLite expansion 5125 -> 5137 bytes; entropy up to 6.3 MB; DB1/DB2,
  DB2 absent and opaque bytes. Same matrix passes on the test-only forced-moving-realloc executable.
- 25 new disposable real-save copies passed actual JS Gear edit, save generation and Python verified native
  publication; exactly one chosen stat changes. All 27 original input hashes remained unchanged.
- `py -3.12 -m pytest tests -q`; `npm test`; `npm run build`; `build_release.bat`;
  `python scripts/verify_release.py --release release --commit <exact-head>` are the release checks.
- Release verification reads the PyInstaller archive, checks embedded/public asset byte equality,
  validates the promoted converter hash and rejects Oodle, personal-save/database/config files.
- Public CI lacks the proprietary Oodle runtime. Its native helper and compilation results are distinct
  from the local Oodle evidence. Synthetic fixtures and public source only are eligible for upload.

## Remaining game acceptance, executable checklist

Use a backed-up disposable ordinary Steam/Epic save profile with Steam Cloud disabled. The user has
authorized sacrificing local saves and disabling Steam Cloud for QA. Do not test WGS write-back.

1. Load an untouched copied save in the installed game, record baseline backpack Offense/Defense,
   equipped totals, level, XP and talent counts. Produce one manual baseline save and exit the game.
2. Open that copy with this exact candidate. Edit one unequipped backpack item's Offense by +1; Apply,
   Download Save. Reopen in editor and compare exported DB1/DB2; preserve the baseline backup.
3. Load the edited copy in game; open all six Gear categories including gloves, equip/unequip the chosen
   item, verify values/totals and absence of crash, manually save, exit and reload. Record whether the
   stored change survives or is recalculated. Do not label a recalculated value as editor persistence.
4. Repeat opening/publishing one already-decompressed older save copy. Verify game load/save/reload.
5. Rename gate: create separate ASCII, accented and non-BMP character-name samples via the game;
   record DB1, metadata and SaveGameList transitions. Identify historical/active index consumers and
   prove crash-recoverable multi-file update before implementing any writer. Current UI stays read-only.
6. Merlin/Butterfly gate: obtain snapshots before discovery, activation, solve, reward claim and reload;
   compare DB1, DB2, collection/reward/XP counts per location. Implement only proven transitions,
   including already-completed/no-op cases and repeat-save idempotence. Current candidate has no writer.

Until observed game outcomes are recorded, Gear gameplay and converter game loading remain
NOT_EXECUTED. The narrowed candidate can be reviewed; it cannot be presented as full mission completion.
