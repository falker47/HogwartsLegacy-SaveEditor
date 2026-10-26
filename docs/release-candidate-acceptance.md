# 1.0.7-rc1 acceptance — 26 October 2026

**Release readiness: NOT_READY for the complete requested Nexus scope; accepted for reduced-scope
publication on 26 October 2026.** The maintainer accepted the candidate and authorized publication
after the recorded Windows/game QA. PR #26 is the single integration path; archive PR #27 remains
separate. Version 1.0.7-rc1 and the exclusions below are retained. The artifact's QA-MANIFEST.json
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
| Gear stat editing, cerealkiller667, 15 Oct | PR23 composite GearID+GearVariation+slot targeting; stat-only atomic batches | 25 copied saves with full DB/opaque comparisons; downloaded RC UI edit and actual game load/equip/unequip/save/restart/reload | PASS for the tested stat edit; see bounded live-game evidence below |
| Gear-slot crash, arftrolizia, 22 Oct | No speculative patch attributed to this report | All six categories, including gloves, opened in the edited live save without a crash; no reporter fixture/reproduction | NOT_REPRODUCED; not claimed fixed |
| Complete Merlin/Butterflies, slmenzies, 14 Oct | PR24 read-only anonymous probe integrated | Probe schema/catalog tests; no writer | NOT_IMPLEMENTED. Requires controlled solve/reward/collection/save/reload transitions in both DBs |
| Already-decompressed saves, PR22 real-copy finding | Validated raw staging without converter output assumption | Four older raw saves among 25 real-copy cases; raw-layout and malformed-layout tests | FILE-LEVEL PASS for verified layout; unsupported layouts rejected |
| Native converter failure, PR25 QA reproduction | HL-02C realloc-source and HL-02D checked output growth promoted with HL-02A | Real Oodle: 11 synthetic cases x5 cycles, repeated with forced-moving allocation; source/DB1/DB2/tail exact; published edited save loads in game | PASS on tested corpus and live save; no universal malformed-save certification |
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

## Observed Windows/game acceptance

Executed on 26 October 2026 using the downloaded PR26 artifact from commit
`b46f6a169af5e0d0e8c30ea9db812a6c41b832ab`, EXE SHA256
`d51656f31859e5c013c0040e1165a607d95bb4b9224dc3f774734e86ed6ddab1`.
The subsequent evidence/acceptance revisions change release documents, not application code or assets.
Game: Steam build 20773316, title version 1613387. This is one real profile and one edited item,
not exhaustive certification of every save, item, platform or existing editor feature.

- Steam Cloud was visibly disabled with user authorization. All 97 pre-session save/backup/index files
  were copied and hashed before launch. The editor worked on an isolated copy of a newly created manual slot.
- The downloaded Windows EXE opened its manager, detected the copied profile/save, created a backup,
  decompressed the save and opened its embedded editor successfully.
- In the actual UI, `Hand_025_Rare` level 38, backpack slot 9, Offense 71 was changed to 72 using
  Apply and Download Save. Publication completed normally. Full decoded comparison found exactly that
  one DB1 field changed; every other DB1 table/field, DB2 and opaque bytes remained unchanged.
- The reconstructed save loaded in the game. The Crimson Quidditch Gloves tooltip displayed 72.
  Equipping/unequipping changed total Offense 253 -> 181 -> 253; Defense remained 291.
  Hands, face, head, neck, back and outfit categories all opened without a crash.
- A new manual save written by the game retained `OffenseStat = 72`, verified directly in its DB.
  After a complete process exit and fresh launch, it loaded again with Offense 253 / Defense 291.
  The glove still displayed 72 and removing it reduced Offense to 181 again. Persistence PASS.
- After QA, the game was closed and all 97 original files were restored with matching SHA256 hashes
  and exact original file set. The two extra QA saves and session evidence were preserved privately.
  Steam Cloud remains disabled. No personal saves, names, screenshots or proprietary DLL are published.

The Windows candidate was accepted for publication with this reduced scope. Full mission readiness
remains NOT_READY because the rename, completion and quest writers below are absent. The absence of
those writers is explicit, not concealed by the successful converter/Gear tests.

## Remaining acceptance for excluded or partially verified scope

Use a backed-up disposable ordinary Steam/Epic save profile with Steam Cloud disabled. The user has
authorized sacrificing local saves and disabling Steam Cloud for QA. Do not test WGS write-back.

1. Older already-decompressed saves: file-level staging/publication passes on four real copies;
   a dedicated old-format game load/save/reload remains unexecuted. Do not generalize the modern-save
   live test to every historical format.
2. Rename gate: create separate ASCII, accented and non-BMP character-name samples via the game;
   record DB1, metadata and SaveGameList transitions. Identify historical/active index consumers and
   prove crash-recoverable multi-file update before implementing any writer. Current UI stays read-only.
3. Merlin/Butterfly gate: obtain snapshots before discovery, activation, solve, reward claim and reload;
   compare DB1, DB2, collection/reward/XP counts per location. Implement only proven transitions,
   including already-completed/no-op cases and repeat-save idempotence. Current candidate has no writer.

4. Report-specific Gear crash: obtain the reporter's reproducible input and actions. The six-category
   smoke test above is evidence for that sample, not proof that the original reported crash is fixed.
