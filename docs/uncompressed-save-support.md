# Already-uncompressed save compatibility — 25 October 2026

Base: main 6a1fc9cd901cdb45a91a300e29a71cb00a35ad90.
Branch: codex/uncompressed-save-support.

## Actual reproduction

Four of 25 authorized ordinary save copies were already-uncompressed GVAS with valid raw SQLite DB1/DB2 arrays. The pinned hlsaves executable returns exit code zero and reports that decompression is unnecessary, without creating the requested output. App._extract_and_edit required that fresh output and therefore refused to open these otherwise supported inputs.

This is a demonstrated compatibility defect. It is not attributed to the generic Nexus No saves found or First page doesn't work reports: their exact current reproductions are still missing.

## Conservative fix

src/save_format.py recognizes only bounded GVAS v2 PersistentGameData containing both expected, unique byte-array images in the order/layout supported by the embedded writer. It validates exact array lengths, SQLite page size/count and integrity entirely in memory. An explicitly empty DB2 is preserved; absent DB2, other versions/classes, corrupt images, duplicate arrays and unsupported layouts do not use the bypass.

The reader's parsed count/size locations must agree with the inherited frontend scanner and fixed header offsets, including zero property GUID flag and DB1-before-DB2 order. Independent review exposed three broader layouts that a tagged reader could accept but the frontend cannot preserve: reversed images, per-tag GUIDs and earlier opaque marker decoys. Three regressions failed before this acceptance guard and pass afterward. The frontend writer is not broadened or replaced.

After the existing verified exclusive backup and session snapshot, validated raw bytes are copied exactly to the new session .decomp path through write_new_verified. Compressed or unsupported input stays on the existing converter path. No fallback trusts stdout, a mere GVAS/SQLite signature, or missing converter output. Saving still stages a compressed candidate, requires exact native decompression, rejects stale sources and publishes one file with existing integrity protections.

## Evidence

- Initial synthetic reproduction: two valid-input launch tests failed before implementation.
- Boundaries added before tightening checks: missing secondary image and trailing SQLite bytes failed the conservative expectations; subsequent tests also cover empty DB2, corrupt images, truncated metadata, duplicates, decoys, property GUIDs, reversed order, disk-full and permission failures.
- Final full Python suite: 202 passed on Python 3.12; no skipped cases. Existing backup, raw-export, converter failure, interruption, rollback/cleanup, concurrent publication and WGS export regressions remain included.
- Actual copies: exactly the four old raw inputs are recognized; the other 21 remain on the converter path.
- Production frontend/manager and native Python publication were exercised separately on 25/25 disposable candidates, including all four older inputs. Every candidate passed exact native round-trip verification, SQLite validity, DB2/opaque preservation and selected-row-only comparison. All 27 original source hashes remained unchanged.
- compileall and git diff --check pass. Native game/menu acceptance is not inferred.

No converter package/hash, Oodle source, dependency, WGS path, profile, index or personal config is changed. No personal save/database/identifier/DLL is included.

## Nexus residuals and release boundary

The [current Nexus posts](https://www.nexusmods.com/hogwartslegacy/mods/2414?tab=posts) confirm the existing rename, Gear and Merlin/Butterfly threads, the export-only Xbox limitation, the already-published replies and the newer 22 October gear-slot crash report. No reply was sent again.

The public Bugs view could not be fetched reliably in this run, and no detailed current reproduction of First page doesn't work or generic No saves found was obtained. They remain unverified, distinct from already-validated Game Pass export and from this specific raw-input failure. Existing v1.0.6 progression, Wand/Revelio, Galleons, Wiggenweld and export fixes are retained; this patch makes no new claim to close those reports.

The Steam game is now installed (build 20773316); no isolated game session was established. Gameplay checks remain NOT_EXECUTED / HUMAN_GATE. Keep the patch Draft and test the consolidated QA candidate before any public release.
