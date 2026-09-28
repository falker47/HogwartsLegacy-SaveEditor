# Residual Nexus audit after v1.0.5

Audit date: 2026-09-28. Base: `642755596cb6f2dff390f178d6db6874e6a89e4b`.
This is a source review/containment pass, not release certification or an in-game PASS.

## Baseline and preservation

The canonical origin was fetched with pruning. Remote main and the lightweight
`v1.0.5` tag both matched the base above. GitHub reported the release published,
not draft/prerelease; PRs #6/#7/#8 merged; CI #13/#14 successful. The release asset
`HogwartsLegacy-SaveEditor-v1.0.5.zip` is 46,624,445 bytes with SHA-256
`4d86de1553682a1470ce75e81e27af14f0724780050a9823421f4d8c03f293bd`.
The existing local ZIP also matched that digest.

Preflight found no tracked or non-ignored changes. Local main was nine commits
behind; it was fast-forwarded, then `fix/nexus-residuals` was created. Switching
through stale main removed the previously ignored runtime `assets/hlsaves.exe`
because that old revision tracked it. The pinned patched binary was restored
from the existing release directory and verified against the vendored hash
`bdf28ae18dc5ecf049af37ca863085851f2cd0f5b22895f9637c5820c8d0f70e`.
Existing ZIPs, build directories, dependency installations, DLL copies and user
configuration were retained; builds use a separate ignored output directory.
Only the tracked embedded HTML is regenerated. No release/tag/report is changed.

## Evidence and decisions

Evidence classes below are deliberately separate:

- **Implementation:** source/history show what this editor does, not what the game accepts.
- **Synthetic database/file tests:** prove deterministic changes and containment only.
- **Public reverse engineering:** useful corroboration, not current gameplay certification.
- **Real-save-file inspection:** read-only inspection of the previously authorized HL-02B
  exported DB; mutations and compression checks only on new disposable copies.
- **In game:** not executed in this pass. No personal save, player data, path or fixture
  is committed or uploaded.

### NR-01 — Game Pass / Microsoft Store

Original: [Nexus posts](https://www.nexusmods.com/hogwartslegacy/mods/2414?tab=posts),
2026-08-28, saves cannot be found. Current discovery checks numeric Steam/Epic
directories and loose `.sav` files only.

The [Game Pass migration tool](https://github.com/Prasath-sk-14188/Hogwarts-Legacy-xbox_to_epic_save)
documents `Packages/WarnerBros.Interactive.PHX_ktmk1xygcecda/SystemAppData/wgs`
and export by internal save identifiers. It does not establish a safe reverse
write-back protocol. Microsoft's [GameSaveContainer API](https://learn.microsoft.com/en-us/uwp/api/windows.gaming.xboxlive.storage.gamesavecontainer)
describes container/blob updates and atomic writes; ordinary file replacement
does not implement that contract. No authorized WGS payload/container fixture was available.

**CODE_VERDICT: SAFELY_CONTAINED_UNSUPPORTED_WGS.** The app detects the known title
WGS directory separately and explains that import/editing is unsupported. Steam/Epic
numeric-folder ordering, `.sav` filtering and Browse remain. Browse/config selection,
refresh, extraction, full-save write-back and raw-export destinations reject recognized
WGS paths before creating backups or payload files. Resolved aliases and copied user
directories with index metadata are covered. Rejected Browse clears previous selection.
There is no speculative payload sniffing, automatic import, rename, metadata editing
or manual replacement recipe.

**IN_GAME_VERDICT: NOT_REQUIRED** for the containment; a future WGS implementation
requires separate format fixtures and in-game/cloud-sync validation.

Tests: title-specific detection, WGS-only and coexisting Steam folders, numeric ordering,
Browse/config rejection, ordinary `.sav` fallback, stale selection, case/metadata/alias
guards, direct API export/write-back refusal and unchanged container sentinels.

### NR-02 — Wand Handles

Original: [Nexus posts](https://www.nexusmods.com/hogwartslegacy/mods/2414?tab=posts),
2026-07-22, both unlock and lock-back ineffective. History: `3facb07` added the guessed
`WandHandles` mutations; `3768e2a` added category-wide lock-back. Current code uses
collection and loot updates, without corresponding usage locks.

The [original reverse-engineering discussion](https://fearlessrevolution.com/viewtopic.php?start=135&t=23361)
uses `WandStyle` plus locks selected from `LockDefinition`. The inspected HL-02B DB
has `WandStyle`, no `WandHandles`, and no `LockDefinition`. Its 84 wand collection
rows comprise duplicate item identifiers with 42 `Obtained` and 42 `Unknown`
states, distributed across exploration and mission subcategories; all identifiers
join usage locks. This establishes that renaming the category alone is inadequate.
It does not establish how to revert mission ownership, duplicate states or prior locks.

[Upstream HLSGE's published feature history](https://www.nexusmods.com/hogwartslegacy/mods/77)
describes general gear/trait/spell/transfiguration locks, not this downstream collection
operation. The repository credits an ekaomk project, whose public code uses a different
frontend; it is not independent proof of these downstream SQL recipes.

**CODE_VERDICT: SAFELY_DISABLED_UNVERIFIED_TRANSITIONS.** Both UI actions are removed
and replaced by an unavailable explanation. Both DB entry points explicitly reject,
including through the manager. No `WandStyle` rename, broad lock wildcard, loot insertion
or category-wide reset is substituted. Restore a backup to undo earlier edits.

**IN_GAME_VERDICT: NOT_REQUIRED** for disabling the action. Re-enabling requires a
separate controlled before/after in-game experiment for both acquire and revert.

Tests: synthetic databases include both actual and formerly guessed categories,
duplicate obtained/unknown rows, existing loot and unrelated locks/categories. Each
unlock/lock call rejects and preserves the entire exported SQLite byte sequence.
An isolated run against base code reproduced success with unchanged `WandStyle` rows.

### NR-03 — Field Guide / Revelio pages

Original: [Nexus posts](https://www.nexusmods.com/hogwartslegacy/mods/2414?tab=posts),
2026-07-03, page unlock has no effect. `d36c4a9` added `RevelioPages` and speculative
loot writes. The inspected DB has no `RevelioPages`; its exploration categories
contain lore collection entries. This is not evidence for changing every exploration row.

[Legilimens source at 707cd14](https://github.com/Malin001/Legilimens-Hogwarts-Legacy-cpp/blob/707cd14c578699d564e9ad7b0748b7532166cd2f/collectibles.cpp)
distinguishes Revelio via `CollectionDynamic`, flying pages via `MapLocationDataDynamic`,
and moth/brazier/statue pages via `MiscDataDynamic`. These are reader queries, not a
verified mutation/reward recipe. [Additional format notes](https://github.com/producedbytmsh/hl-savetools)
describe challenge/reward event state and claim interactions between both databases.
Those claims were not independently gameplay-verified here and do not justify extra writes.

**CODE_VERDICT: SAFELY_DISABLED_UNVERIFIED_TRANSITIONS.** The card is now
“Revelio Pages — unavailable”; it distinguishes other page types and explicitly says
page challenges/XP are not completed. Both unlock and lock DB methods reject. The
speculative collection/loot operations are removed. No legitimate pages are reset.
The shared collection copy also no longer claims that locking is a verified quest repair.

**IN_GAME_VERDICT: NOT_REQUIRED** for disabling. Any future narrower Revelio feature
must separately prove lore visibility, rewards/challenges, and non-destructive revert.

Tests: both API directions preserve exact database bytes, including real-style lore
categories, legacy guessed rows, unrelated loot and locks; UI has no mutation bindings.

### NR-04 — Experience and Talent Points

Original: [Nexus posts](https://www.nexusmods.com/hogwartslegacy/mods/2414?tab=posts),
2026-06-11, progression editing before normal talent unlock followed by broken points.
The report is a correlation, not proof of a particular prerequisite flag or repair.

The baseline manager always calls XP, perk, both name, inventory and house setters;
the house setter also inserts floo locks. A synthetic SQL update trigger reproduced
XP/perk writes when only the first name was changed. Real DB schema confirms
`MiscDataDynamic` is keyed by **DataOwner + DataName**, with identity/house under
`Player`, XP/level under `ExperienceManager`, and points/capacity under `Player0`.
No reliable talent-unlock predicate or safe automatic repair was established.

**CODE_VERDICT: DIRTY_WRITES_FIXED_PROGRESSION_READ_ONLY.** The Player page sends
only dirty fields and shows errors without resetting unsaved edits. Reads and the new
atomic patch target the verified owner/key pair. The backend compares actual values,
validates the entire request before writing, rejects unknown/missing/ambiguous fields
and rolls back SQL failures. It does not insert missing defaults or grant floo locks.
Experience, Talent Points and internal Level changes are refused by this form's backend;
the first two remain visible/read-only with an explicit prerequisite/repair warning.
Capacity accepts decimal integer strings in `0..2147483647`: a storage-validation bound,
**not** a guarantee that arbitrary capacities are useful in the game.

Existing lower-level editor helpers and advanced custom database imports are not a
consistency repair API and remain outside the guarded Player form. The unrelated
Talent deletion page is unchanged. No spent/unspent-point recalculation or quest edit
has been introduced. Already damaged saves are not repaired by opening or applying.

**IN_GAME_VERDICT: REQUIRED_BEFORE_RELEASE** for the changed Player apply path,
using the short checklist below; not executed here.

Tests: actual Vue setup → manager → SQLite; change/reset/change-back/no-op; trigger
proof of no XP/perk UPDATE; owner isolation; whole-request rejection of negative,
fractional, blank, non-finite, exponent, whitespace, overflow and non-string numbers;
integer boundaries; blocked progression fields; absent keys/null-safe reads; SQL rollback.
On a disposable real DB, a capacity-only patch changed exactly one intended row across
all tables; XP, points, collection/lock state and DB2 were unchanged. Real converter
recompression/decompression reproduced the edited uncompressed save byte-for-byte.

### NR-05 — “First page doesnt work”

The [public bug listing](https://www.nexusmods.com/hogwartslegacy/mods/2414?tab=bugs)
still shows this v1.0.2 report, dated 2026-02-03, as being looked at (three comments).
The retrieved public listing exposes no reproduction steps or detailed comment bodies.
The title alone cannot identify a current defect or link it to the null-safety fixes.

History `2f58c84` (2026-01-20) adds `safeExtract` in `getPlayerData`; `45166c6` adds
missing-result protection to the generic result mapper. These precede the displayed
report date; neither a local source change nor its date proves the affected user's
distributed artifact contained the fix.

**CODE_VERDICT: INSUFFICIENT_EVIDENCE. IN_GAME_VERDICT: NOT_EXECUTED.** Current
synthetic missing-row Player reads pass, with a regression protecting that behavior.
No separate production change is attributed to this report. Obtain the detailed report,
app/game version and repeatable steps before classifying it as fixed or duplicate.
No Nexus/GitHub report has been closed or replied to.

## Verification contract and manual gate

Local verification completed:

| Check | Result |
| --- | --- |
| `python -m pytest tests -q -p no:cacheprovider` (new isolated basetemp) | 65 passed; 52 existing plus 13 new |
| `npm test` | 53 passed; all 30 existing bridge/export cases plus 23 new |
| `npm run build -- --outDir <new ignored directory>` | PASS, 493 modules |
| ESLint against baseline | Same 5 errors; 501 → 467 warnings; no new diagnostics in changed code |
| `git diff --check` | PASS |
| Isolated execution of base source | Reproduced blind progression writes and ineffective wand category update |
| Prior authorized save, read-only schema inspection | PASS; original export hash unchanged |
| Disposable real-save-copy converter round trips | PASS; DB1/DB2 integrity, exact bytes and tail; intended Player row only |

The first frontend build attempt hit esbuild's sandbox ancestor-directory access
restriction; the same isolated build succeeded outside the sandbox. Native UI and
in-game checks below are still pending. Exact PR-head CI results belong in the handoff;
local results do not stand in for pending CI. The Windows packaging check runs through
the existing `release-smoke` job, preserving all prior local release/build artifacts.

All existing Issue #3 Python/Node tests are retained unchanged: both raw DB exports,
exact bytes/hashes and SQLite integrity, cancel/error recovery, existing-destination
and original/backup protection, no raw recompression/write-back, full/custom save
generation, and external/fallback bridges. Existing hlsavetool installer/hash tests
remain unchanged. A separate local real-save-copy round trip additionally verifies
the pinned corrected executable, both DBs, exact decompressed bytes and external/tail
segments. That check uses the prior independent HL-02B parser, not editor comments.

The production HTML must be built from these sources and committed. Build to a new
output folder to preserve the user's prior `dist`/`release` artifacts. CI retains the
existing Python, editor tests/build and full Windows release-smoke jobs. No dependency,
version/tag/release or proprietary DLL distribution is changed.

Before release, after independent review:

1. Launch the candidate manager against an **ordinary disposable copy** of an authorized
   save, with the game closed. Record the original/backup hashes. Open Player: XP and
   Talent Points must be visible, read-only, with the prerequisite warning.
2. Change only First Name, press Reset, verify it reverts. Change only First Name again,
   Apply and download a full save. Reopen it: only that identity field should differ;
   XP/Talent Points must equal the recorded values. A backup must exist.
3. Enter `-1` in capacity and Apply: show a validation error and keep the pending form;
   no database changes. Reset. On Collections, verify both unavailable explanations
   and the absence of Wand/Revelio unlock/lock controls.
4. Browse to a **synthetic** `SystemAppData/wgs` folder with index/payload sentinels:
   show the limitation, clear any prior selection, create no backup/output there.
   Browse back to the ordinary copy and verify selection works.
5. In a controlled game session, load the name-only edited copy using the normal
   Steam/Epic save workflow. Check the name, unchanged XP/Talent Points and normal
   save/reload. Restore the original test copy/backup afterward. Do not test WGS
   replacement or attempt disabled unlocks. This is the only required in-game gate
   introduced by this patch; it does not certify every existing editor feature.

This checklist remains unexecuted in-game. Re-enabling the disabled features and
repairing saves already affected by progression edits are separate research tasks.
