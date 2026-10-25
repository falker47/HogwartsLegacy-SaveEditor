# Already-uncompressed save compatibility plan

Goal: open valid older GVAS saves whose raw SQLite arrays require no decompression.
Evidence: four authorized copies cause the pinned hlsaves converter to return zero with an already-uncompressed warning and no destination file; current App therefore refuses them.

- [x] Reproduce with tagged synthetic GVAS and actual SQLite; two expected launch tests fail on main.
- [x] Recognize only bounded GVAS v2 PersistentGameData tags, exact array lengths and in-memory SQLite integrity. Do not trust stdout, raw signatures in opaque bytes or absence of converter output.
- [x] Exclusively stage the verified snapshot through write_new_verified; preserve all backup, source-snapshot, WGS and publication checks.
- [x] Test absent/empty DB2, malformed/corrupt/duplicate arrays, opaque decoys, staging faults and compressed-path regressions.
- [ ] Run full Python suites, frontend regression/build via integrated QA, native disposable-copy checks and draft-PR CI.

No relation to the un-reproduced Nexus first-page or generic no-saves reports is claimed. No game files or config.json are written.


Ruling: require both image tags because the embedded editor locates both arrays. An absent DB2 remains unsupported by this compatibility bypass; an explicitly empty DB2 is preserved. SQLite header page size/count must exactly cover each image because integrity_check alone accepts trailing data.

Review fix: the first reader accepted property GUIDs, reversed images and opaque marker decoys that the inherited frontend cannot preserve. Three failing regressions confirmed the finding. Require exact agreement with the frontend scanner count/size offsets, zero property-GUID flag and DB1-before-DB2 order; do not widen the frontend writer.
