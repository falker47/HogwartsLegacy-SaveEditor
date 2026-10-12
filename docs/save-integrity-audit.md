# Save integrity audit — 12 October 2026

Base: `e8fdbff851bfb547f713a34cf2393007f54f9541` (current main, after v1.0.6).
Scope: save selection, backups, temporary inputs, compression/publication, raw SQLite
exports and Game Pass/WGS exports. No editing SQL, progression safeguards, collections,
browser metadata semantics, dependencies, versions, release workflows or third-party
components are changed. Trello: https://trello.com/c/SzSh96gk.

## Preflight and execution record

- Fetched origin. Local main was behind; the primary checkout was on
  `feat/game-like-save-browser` with a user change to `assets/HLSGE.html`.
  That checkout/change and unrelated worktrees were left untouched.
- Created an attached isolated worktree at `origin/main`, then branch
  `codex/save-integrity-audit`. No main switch/reset, merge, release or tag.
- Read README, residual Nexus audit (including superseding v1.0.6 acceptance), Game
  Pass export/browser documentation, converter provenance, relevant Python/Node tests,
  `editor.py`, `app.py`, `save_paths.py`, `save_browser.py`, frontend save generation
  and bridge dispatch, and both workflows.
- Main CI run [36999760881](https://github.com/falker47/HogwartsLegacy-SaveEditor/actions/runs/36999760881)
  was successful on the exact base. Baseline Python suite: **144 passed**.
- CAPABILITY_BOOTSTRAP_V1: NONE. Existing tools/runtimes and the repository lockfile
  suffice. No new service, plugin, proprietary DLL or native game fixture acquired.

## Complete data path

1. `SaveBrowser.discover` reads metadata and caches by path/size/timestamps. The App
   pins the exact selected path and backup folder before starting its worker. WGS
   guards run before ordinary extraction/backup, save publication and raw exports.
2. The worker reads the selected ordinary save once. It exclusively creates a
   timestamp + UUID backup in `Backups`, flushes/syncs it, and reads it back for exact
   byte comparison. Failure stops extraction. The temporary compressed input uses
   the very same bytes, so the backup corresponds to the editor's source snapshot.
3. A unique `temp/edit-*` directory holds compressed input, decompressed GVAS and
   IPC status. `hlsaves -d` must succeed and create fresh, nonempty GVAS output.
   The editor receives the compressed snapshot path as well as the original path.
4. Existing Vue/sql.js editing and full/custom DB1/DB2 generation remain unchanged.
   Both external and fallback bridges route full saves to `save_edited_file`; raw
   databases use `export_database` and never trigger save compression/publication.
5. `EditorApi` validates strict base64 and a nonempty GVAS envelope and compares the
   current source SHA-256 to the session snapshot. It creates a unique `.hl-edit-*`
   directory beside the destination (same filesystem), verifies the staged edited
   bytes, and asks `hlsaves -c` to write a fresh candidate, never the original.
6. `hlsaves -d` reads that candidate into a fresh verification file. Both converter
   calls must succeed with nonempty output; verification must equal the supplied
   edited bytes exactly, including DB2 and the tail. The candidate is synced. A
   second comparison rejects an original changed while conversion was running.
7. `os.replace` publishes the complete candidate. Pre-publication failures keep the
   original unchanged; there is no destructive write followed by best-effort restore.
   The candidate digest becomes the session's next expected digest. Cleanup/status
   failures after successful publication cannot misreport it as a failed save.
8. Normal editor closure removes that session's temporary directory; extraction
   failure cleans it immediately. The browser fallback retains its unique directory
   because the user still needs its drag-and-drop input.

## Reproduced defects and targeted fixes

Tests were run against the old implementation **before** applying each fix. The
first complete probe produced **18 failures / 4 passes**, exposing these defects:

| Defect | Reproduction | Correction |
| --- | --- | --- |
| Converter failure truncates original | Write a prefix then exit nonzero / raise ENOSPC | Candidate staging and atomic publication |
| False success for missing/empty/truncated converter output | Exit zero without output, or emit a prefix | Fresh output checks and exact decompression round trip |
| Corrupt bridge input reaches converter | Invalid base64, empty/non-GVAS or raw SQLite | Strict decoding and GVAS envelope check |
| Stale editor overwrites newer source | Change source after editor creation / during conversion | Snapshot SHA-256 comparisons before conversion and publication |
| Shared decompression reused or overwritten | Leave a prior `.decomp`, then converter emits nothing | Unique per-session input/output/status paths |
| Empty/corrupt decompression launches editor | Exit zero with invalid output | Reject missing, empty and non-GVAS output |
| Backup collision overwrites prior backup | Two different sources at the same frozen second | Exclusive timestamp + UUID backups, verified against source bytes |
| Short WGS or raw DB writes reported successful | Writer returns fewer bytes without raising | Check count, flush/fsync, compare destination bytes/hash, roll back |

Additional probes reproduced status/cleanup failures misreporting a committed save,
catchable WGS interruption skipping rollback, and overlapping same-session calls
replacing a completed save. Fixes isolate status callbacks, distinguish publication
from cleanup, roll back on `BaseException`, pin each call's expected digest and
refuse overlapping same-session transactions with a per-instance lock. Independent
review reproduced two actual threads both passing the final digest check; its
regression now confirms that only the first transaction publishes.
Windows requires a writable handle for `fsync`; candidate synchronization uses
`r+b`, verified on the local Windows runtime.

## Automated evidence and limits

All newly executed save data is generated synthetic bytes/SQLite, in pytest/Node
temporary directories. No personal save, account identifier or game data was read,
modified, committed or uploaded. The converter in save tests is a deterministic
test double exercising actual Python file writes, flush/sync, rename and cleanup.
It is **not evidence of native Oodle format compatibility or gameplay acceptance**.

`tests/test_save_integrity.py` adds 42 cases. The existing API/Node harness now models
staged conversion and round-trip output, asserting actual full/custom published
bytes, unchanged raw-export sources/backups, status and close behavior for both
bridge variants. Existing progression/resource/collection tests remain required.

| Fault / contract | Evidence |
| --- | --- |
| Converter exit/spawn failure, ENOSPC, EACCES, missing/empty/truncated output or wrong round trip | Failure result; original exact bytes retained |
| Malformed save payload | No converter call or source modification |
| Atomic replace EACCES/ENOSPC | Original exact bytes; temporary cleanup; later retry succeeds |
| Original changed before/during conversion or overlapping saves | Preserve the newer bytes; reject stale publication |
| Exclusive copy write/flush/fsync/readback failure | Newly created partial removed; source unchanged |
| Existing destination | Exclusive creation refuses without overwriting/removing existing content |
| Backup failure / same-second sessions | No extraction on failed backup; two independent complete backup/input sets |
| Manual restore of generated backup | Copy back onto a disposable edited fixture; original exact bytes restored |
| Hard process termination during candidate writing | Child exits 86; original intact; orphan candidate isolated; retry does not reuse it |
| WGS short write, disk full, denied output, wrong destination hash, catchable interruption | Entire new output set rolled back; original payload/index/metadata bytes and mtimes unchanged |
| WGS existing/racing target, source mutation, ambiguous identity, links, limits, cleanup ownership | Existing regressions retained; only owned outputs removed |
| Post-publication status/cleanup error | Save still reported committed; cleanup error exposed as warning |

No restore API exists in v1.0.6: **Open Backups** opens a folder. The restore probe
demonstrates the backup's byte content is usable for a manual copy, not an automatic,
atomic restore feature. No speculative restore implementation was added.

Local final verification:

| Check | Result |
| --- | --- |
| `py -3.12 -m pytest -q` | **186 passed**, no skips; baseline 144 + 42 new fault cases |
| `npm.cmd test` | **58 passed**, no skips; both bridge variants and v1.0.6 editing regressions |
| `npm.cmd run build` | PASS, 493 modules, single-file editor |
| `build_release.bat` | PASS on final code; Python 3.12 tests, Vite, PyInstaller and package assembly |
| Package required files, converter SHA-256 and Oodle exclusion | PASS; converter remains `bdf28ae18dc5ecf049af37ca863085851f2cd0f5b22895f9637c5820c8d0f70e` |
| `py -3.12 -m compileall -q src` / `git diff --check` | PASS |
| Independent read-only review | No unresolved Critical/Important findings; reproduced concurrency race corrected; cleanup reporting also corrected with regression |

The first native packaging attempt inherited an incompatible PowerShell module
environment and could not discover `Get-FileHash`. Running the unchanged batch
script from a Python subprocess with `PSMODULEPATH` omitted, exactly like existing
installer tests, passed. This is process-local environment isolation, not a build
script/product change. No dependency pins were changed and no DLL was acquired.
The rebuilt HTML is local packaging output; the tracked HTML is retained byte-for-
byte from main because frontend product sources did not change.

Exact PR-head CI belongs in the delivery handoff and GitHub checks; main's prior CI
does not establish the candidate's remote result.
Python 3.14 and Node 22 are also installed locally. CI uses Python 3.12, Node 20 and
a full Windows packaging smoke.
An initial test rerun exposed a legacy unmocked GUI error dialog; the headless fixture
now mocks all dialogs. A child-process probe explicitly supplies DEVNULL stdin for
Windows pytest capture. Neither runner issue is classified as a product bug.

## Game Pass and prior real evidence

WGS source reads stay bounded and read-only. Exports retain exclusive `.sav` creation,
source digest recheck, ownership-aware rollback and WGS path rejection. Added output
verification never writes an index, container metadata, WGS payload or Xbox cloud.
Exported ordinary copies alone can enter the editor. Synthetic source snapshots
compare complete bytes and mtimes across success/failure; write traps reject attempts
to open fixture WGS sources in a write mode.

Prior real acceptance is separate: the residual audit, converter provenance and
Game Pass document record disposable native converter exact round trips, focused
v1.0.6 in-game save/reload and real Game Pass export acceptance on **29 September
2026**. This pass did not rerun those checks or upgrade them to certification of
the new publication flow. No DLL was sourced or distributed.

## Residual risks / demonstrated guarantee boundary

- A GVAS signature is an envelope check, not full structural/SQLite validation.
  Exact converter round trip detects incomplete transformations but cannot certify
  game semantics, SQL edits, hostile input, or defects shared by converter modes.
- Atomic publication relies on local filesystem `os.replace` semantics. File data
  is synced before publication; parent-directory durability, power loss, faulty
  storage, network filesystems and hardware/filesystem corruption are not certified.
- SHA-256 checks catch observed changes; they are not a lock/CAS against the game or
  another process. A write in the final check-to-replace interval can still be lost.
  Close the game before editing/exporting. Path/junction swaps in that interval are
  likewise not excluded by path preflight. No cloud coordination is implemented.
- Hard termination bypasses cleanup. Ordinary saves remain untouched until rename;
  orphan stages/session files may remain. A WGS/raw export destination may retain
  partial copies after hard kill/power loss; WGS originals remain untouched. Export
  batches are not atomically visible and concurrent readers can see incomplete copies.
- Cleanup can fail because of permissions or concurrent access; it is reported.
  Ownership checks preserve files replaced by another process, but are not a lock
  against races between identity checking and deletion.
- Backups are exact copies of the selected input, including any corruption already
  present. Same-volume backups do not protect from device failure; no retention,
  automatic repair or crash-safe manual restoration is claimed.
- Direct API use depends on the caller for a backup; the normal App flow verifies a
  backup before launch. Cancellation and failed conversion do not discard a valid
  backup. Status IPC remains advisory; interrupted/partial messages cannot authorize
  writes, and status loss cannot undo a successful publication.
- Current native converter/Oodle, packaged UI and in-game loading of this candidate
  were not exercised here. Existing third-party licensing/distribution boundaries
  remain unchanged. No release is published and no PR is merged by this audit.
