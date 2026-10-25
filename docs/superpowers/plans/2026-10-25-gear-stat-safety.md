# Gear stat safety Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline. The user's mission explicitly requests autonomous execution and authorizes focused draft PRs after verification.

**Goal:** Make existing backpack OffenseStat/DefenseStat edits target exactly the selected inventory item and fail without partial changes.
**Architecture:** Join InventoryDynamic to GearItemsDynamic on ItemID/GearID and Variation/GearVariation. Validate an entire stat-only patch batch and its unique Player0/ActorBackpack references before one SQLite transaction. The Vue page derives dirty stat patches, shows load/apply errors, and preserves pending edits on failure.
**Tech Stack:** Vue 3, TypeScript, sql.js, node:test, pytest, Windows.
**Spec:** Mission priorities B and D; observed composite GearItemsDynamic primary key and InventoryDynamic (CharacterID,HolderID,SlotNumber) key. No gameplay cap, total-stat recalculation, gear-level edit, or in-game crash fix is inferred.

## Global Constraints

- Use synthetic public fixtures; real authorized copies and reports stay under ignored temp/.
- Do not read config.json or modify original saves, WGS or other profile folders.
- Branch codex/gear-stat-safety starts at main 6a1fc9cd901cdb45a91a300e29a71cb00a35ad90.
- Rename protection stays in PR #21; unrelated changes are not added there.
- Only OffenseStat and DefenseStat may change. Nonnegative signed-32-bit bounds are storage validation, not certified game limits.
- No public release, merge or Nexus messages.

## Review Focus

- Same variation across different GearIDs: exact pair selection and mutation.
- Shared/stale/ambiguous inventory references: reject before any UPDATE.
- Malformed stats and a later SQL failure: preserve all rows in the batch.
- A single dirty stat: preserve the other stat, traits, rarity, level, DB2 and opaque save bytes.
- Load/apply errors: visible feedback, unsaved inputs retained, Reset reloads committed values.

### Task 1: Composite-key, stat-only atomic editing

**Files:** HLSE-src/src/client/interfaces/gear.ts, resources/saveGameDB.ts, managers/saveGame.ts; HLSE-src/tests/gear-stats.test.cjs.
**Interfaces:** getPlayerGearInventory(): Promise<GearItem[]> includes SlotNumber; updateGearItems(items: GearStatEdit[]): Promise<void>; updateGearItem delegates a single patch.
- [x] Write synthetic fixtures with observed schema and duplicate variations; test exact join, exact UPDATE, readonly preservation and malformed/shared/stale target rejection.
- [x] Run new tests against main; verify failures reflect unsafe existing behavior.
- [x] Implement full-key joins, stat-only patches, numeric validation, membership checks and one batch transaction.
- [x] Verify rollback after a trigger abort and full frontend suite.
- [x] Commit source and regression tests.

### Task 2: Gear Apply/Reset and visible limitations

**Files:** HLSE-src/src/client/pages/playerInventoryGearPage.vue; gear-stats.test.cjs; assets/HLSGE.html.
**Interfaces:** computed GearStatEdit[] from current/original GearItem[]; refreshData/saveData expose errorMessage and ready state.
- [x] Write page-level tests for same-variation independent inputs, dirty-only patches, change-back, Reset and failed Apply/load.
- [x] Observe failing tests, then implement atomic batch Apply and error handling.
- [x] Explain backpack-only stored stats, readonly attributes and unverified game recalculation. Require Apply then save/download.
- [x] Build and synchronize generated HTML. Run frontend, Python, relevant static checks and Windows build_release.bat in this worktree only.
- [x] Commit focused UI/build changes and evidence.

### Task 3: Review and draft PR

**Files:** docs/gear-stat-safety.md.
- [x] Validate production code on new disposable real-save copies; verify all non-target SQLite rows, DB2, tail and native converter exact round trip; re-hash original sources.
- [x] Independently review the branch; fix any material findings with failing regressions.
- [ ] Check private-file exclusion, dependency hashes and QA package contents; record SHA-256.
- [ ] Push and open one focused Draft PR; inspect CI at its exact HEAD.

## Execution ledger

- Baseline main: Python 186 passed; frontend 58 passed.
- Rename PR baseline separately: Python 195 passed; frontend 73 passed.
- Ruling: preserve game originals and use independent copies despite broad sacrificial authorization; in-game work requires demonstrated path isolation.
- Ruling: do not attribute the 22 October Nexus gear-slot crash to this database bug without a reproducible game session.


Local implementation, full tests, native E2E and independent review complete. Push/Draft PR and exact-head CI remain integration steps; gameplay remains gated.
