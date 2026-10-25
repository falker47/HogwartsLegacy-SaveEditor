# Gear Offense/Defense safety — 25 October 2026

Base: main 6a1fc9cd901cdb45a91a300e29a71cb00a35ad90.
Branch: codex/gear-stat-safety. Scope: existing backpack stored-stat editing, not gear creation, level/trait editing or progression repair.

## Reproduced defect

The observed GearItemsDynamic primary key is (GearID, GearVariation), with NOCASE text collation. InventoryDynamic identifies a location by (CharacterID, HolderID, SlotNumber); its ItemID and Variation reference the gear key. The old read JOIN and UPDATE used GearVariation alone, and the page also keyed/de-duplicated pending edits by variation. A single variation shared by different GearIDs could display the wrong item, merge pending changes or update several records.

Authorized real-copy inspection found four repeated variation groups across 25 historical DB1 snapshots, including one incorrect Player0 backpack join row. A synthetic fixture with two player items and another owner's item sharing a variation reproduced the defect before the fix. Initial backend regressions: 28 failed / 2 passed on main. Page regressions separately exposed missing error handling and non-atomic Apply.

## Resulting behavior

- Read JOIN uses both ItemID/GearID and Variation/GearVariation and returns the backpack slot.
- A patch identifies the immutable gear pair and selected slot. Only OffenseStat/DefenseStat are writable.
- Before any UPDATE, every target must be unique and have exactly one unchanged Player0/ActorBackpack inventory reference with Count=1. Missing, moved, equipped, shared, ambiguous, stacked and repeated batch targets are refused.
- Values must be whole decimal integers in 0..2147483647. This is a storage bound, not a verified game cap. Fractional, non-finite, exponent/hex/blank/negative/overflow and wrong-type inputs are rejected.
- All patches validate before one SQLite transaction. A later SQL error rolls back the full batch. A single dirty stat updates only that SQL column; no-op patches cause no UPDATE.
- The page tracks each slot/key separately, derives dirty stat-only patches, retains inputs on validation/SQL failure, reloads committed values on Reset and reports unsupported/missing schemas.
- UI copy explicitly limits this page to backpack DB1 stored values, read-only other attributes, unverified game recalculation/persistence and Apply followed by save/download.

DB2 and the game's derived/equipped totals are not rewritten. The observed DB2 contains some matching gear keys with different historical values, so automatically mirroring edits is not justified.

## Verification

- Main baseline: 186 Python / 58 frontend tests.
- Focused added tests: 35 passed; full frontend: 93 passed.
- Full Python: 186 passed on Python 3.12; no application-Python behavior changes.
- Production frontend build: 493 modules; bundled HTML rebuilt.
- Windows build_release.bat: passed Python, Vite, PyInstaller and package assembly in the isolated worktree. Proprietary Oodle is excluded.
- ESLint comparison: no new errors; changed Gear interface/page have no diagnostics, existing DB/manager warnings decreased. Repository-wide lint still has inherited errors; vue-tsc is blocked by inherited tsconfig reference to missing src/server/server.ts. Neither check is reported as globally passing.
- Independent review: no material Gear defect found; reported trailing whitespace was removed before commit.
- Native disposable-copy E2E: 25/25 candidate saves used production manager/SQL/generator and the actual pinned converter/Python publication path. Each changed exactly one selected OffenseStat value across all DB1 tables, preserved every other logical row/field, DB2 and every non-DB1 byte, passed SQLite integrity and exact native decompression verification. One case included an actual repeated variation.
- All 27 original source files were re-hashed unchanged. No config.json, WGS, original profile or index was written. Real data, identities and DLLs remain outside Git.

Synthetic fault tests additionally cover later-row validation failure, trigger-abort rollback, stale/shared targets, readonly fields, no-op writes and error/reset behavior. Existing save-publication fault injection remains required.

## Remaining gate

Game equip/unequip, effective totals, load/save/reload, rarity/trait interactions and numerical game limits: NOT_EXECUTED / HUMAN_GATE. File-level persistence and a converter round trip do not establish game acceptance.

The [22 October Nexus gear-slot crash](https://www.nexusmods.com/hogwartslegacy/mods/2414?tab=posts) is a separate un-reproduced report; this patch does not claim it fixed. Steam game build 20773316 is installed, but safe game-path isolation from original saves was not established. Keep this change Draft until the requested gameplay checks are performed in an isolated disposable session.
