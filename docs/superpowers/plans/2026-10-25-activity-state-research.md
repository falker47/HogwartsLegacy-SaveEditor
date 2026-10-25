# Activity-state research plan

Goal: make Merlin/Butterfly investigation reproducible without adding progression writers.

- [x] Pin primary reader/catalog revisions and distinguish reverse-engineering claims from verified observations.
- [x] Write five failing synthetic tests for a read-only anonymous DB1/DB2 probe.
- [x] Implement an in-memory SQLite reader; tests pass, full Python suite 191 passed.
- [x] Run on authorized copies: 25 valid pairs, observed states 2/33/34 and 135 differing common Merlin states.
- [x] Document exact missing game experiments and support boundaries; do not infer completion from raw counts.
- [ ] Review, commit and open a focused Draft research PR; verify exact-head CI.

Constraints: no config.json, original saves, WGS, private identifiers or proprietary files in the patch. No completion/reversal writer. User requested autonomous execution; no duplicate mission is created.


Review fix: never stringify unvalidated saved state text; unavailable/ambiguous rows produce no value echo. Empty or unrelated catalogs yield NEEDS_CATALOG. Seven failing regressions were added before the fixes.
