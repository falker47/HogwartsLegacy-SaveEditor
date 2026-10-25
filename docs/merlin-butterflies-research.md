# Merlin Trials and Butterflies: evidence and experiment protocol

Date: 25 October 2026. Base: main 6a1fc9cd901cdb45a91a300e29a71cb00a35ad90.
Status: read-only investigation delivered; completion/reversal writers remain unsupported.

## Reproducible sources

- [Legilimens reader at 02525dde](https://github.com/Malin001/Legilimens-Hogwarts-Legacy-Collectible-Finder/blob/02525dde0fd9bc0be72982478680377dccb41246/legilimens.py): its QUERIES/TABLES mapping reads SphinxPuzzleDynamic rows with EInteractiveState=34 as solved Merlin trials, and EconomicExpiryDynamic row presence for catalogued Butterfly chests. Its COM_11 check is a bug heuristic, not a mutation recipe.
- [The same revision's collectible catalog](https://github.com/Malin001/Legilimens-Hogwarts-Legacy-Collectible-Finder/blob/02525dde0fd9bc0be72982478680377dccb41246/collectibles.json) contains 95 Merlin and 15 ButterflyChest entries. These are public object identifiers, distinct from personal CharacterUIDs. No catalog or personal save is bundled here.
- [Independent reverse-engineering notes at e568dedc](https://github.com/producedbytmsh/hl-savetools/blob/e568dedcda2611f54cc793e6d0237c749ae25094/README.md) discuss DB1/DB2, challenge locks, event-granted rewards and achievement events. These are author observations, not authoritative game implementation. In particular, their blanket advice to apply every edit to both databases is not adopted: different values can be legitimate, and the merge/ownership contract is unproven.

No third-party code or write-back method from these sources was imported.

## Actual structures and limits

| Evidence | Safe interpretation | Not established |
| --- | --- | --- |
| SphinxPuzzleDynamic(SphinxPuzzleGUID, EInteractiveState), keyed by GUID | Read individual raw states; the reader associates 34 with solved trials | State 2 or 33 is not independently certified as discovery/activation; a missing row is not proof of an uncompleted trial |
| EconomicExpiryDynamic(UniqueID, Expiry), keyed by UniqueID | Match only known ButterflyChest catalog keys | This table also holds unrelated economic entries; its total row count is not a Butterfly count |
| PlayerStatsDynamic ActivityName=COM_11, ActivityValue=Complete | Observe a quest-complete marker used by the reader's heuristic | Does not establish which flock spawned, chest was opened, random reward was granted, or quest repair is safe |
| AchievementDynamic, LocksDynamic, MiscDataDynamic, CollectionDynamic, LootItemsDynamic | Candidate dependency surfaces to capture during experiments | Counter changes alone do not prove XP, inventory slots, challenge rewards, collections or achievements |
| Both databases carry these schemas | Inspect both independently | Neither is certified as a disposable mirror, or as the sole source of truth |

The inspected authorized copies contained Merlin states 2, 33 and 34. Across 25 historical saves, 135 common Merlin keys had differing DB1/DB2 states; Butterfly catalog-row presence differed too. These are overlapping historical observations, not 25 independent controlled experiments. The data does not justify synchronizing either database to the other.

Schema validation passed for all 25 DB1/DB2 pairs. No original file was modified; the 27 copied source files were re-hashed after the work. No private names, CharacterUIDs, account paths, raw saves or extracted databases are committed.

## Delivered offline probe

scripts/inspect_activity_state.py reads standalone exported DB copies into in-memory SQLite databases. It never opens a database for writing, creates sidecars, runs a converter, or writes an output file. It reports anonymous raw-state distributions, DB1/DB2 key/state differences and catalog-key presence. Missing tables are UNAVAILABLE, not zero progress. Without a relevant Butterfly catalog, classification is NEEDS_CATALOG. gameplay_completion_verified is always false.

Export DB1 and DB2 separately from an authorized disposable input using the editor's existing raw-export buttons. Save the pinned public catalog separately under ignored temp/, then run:

    python scripts/inspect_activity_state.py --db1 temp/before-db1.sqlite --db2 temp/before-db2.sqlite --catalog temp/collectibles.json

Repeat with the after copies. The output excludes object keys, character names, UIDs and file paths. Preserve hashes and complete table-level diffs locally; anonymous summary counts alone cannot prove that exactly one activity changed. The synthetic regression suite checks state divergence, catalog filtering, absent schemas, corrupt SQLite and source byte/mtime preservation.

## Exact missing experiments

Run only in an isolated game test environment with independent, verified backups. Keep game/Steam build, mods, profile technical identity and chosen object fixed. Do not use display names to associate profiles. Capture complete ordinary save, index and DB1/DB2 at each checkpoint, with hashes; keep all personal evidence private.

1. **Merlin:** capture an unvisited trial, first discovery, activation, solved puzzle, challenge reward claim and subsequent load/save/reload separately. Repeat across a challenge threshold and for a trial after the inventory-capacity challenge is already complete. Compare GUID-specific state plus map discovery, XP, FGC/ACK-style counters where present, locks, inventory capacity and reward/collection rows. Identify which changes the game itself writes to each database and the opaque GVAS metadata.
2. **Butterfly:** capture flock discovery, following, chest spawn, opening and actual conjuration receipt separately, followed by reload. Compare the exact public catalog key, expiry values, map/spawn state, loot and collection rows. Include the COM_11 quest flock and an independent non-quest flock, plus quest-before/after states. Establish behavior when a chest has already awarded a reward.
3. **Reverse edits:** restore a complete baseline test snapshot; do not assume deleting a row or reducing a counter can undo a random reward, quest event, capacity grant or achievement. Test reversibility only after forward semantics and identity are established.
4. **Persistence and collateral checks:** menu/load/save/reload, another character and historical slots, both databases, XP/rewards/challenges and normal live achievement behavior. Save-state counters cannot certify an achievement event.
5. **Only after those observations:** define the minimal writable state, reject missing/ambiguous/unsupported conditions, add regressions and a recoverable transaction if more than one file is actually required. Multiple os.replace calls do not form one atomic transaction.

## Support classification

- Read-only schema/state/catalog inspection: supported as evidence collection.
- Exact completion, rewards, quest repair, inverse transitions or Unlock All: unsupported.
- Controlled in-game pre/post observations for this candidate: NOT_EXECUTED / HUMAN_GATE.
- This research does not change existing Wand/Revelio/progression behavior or claim the v1.0.6 validations were repeated.

The game is now installed, but a demonstrated save-path isolation mechanism was not established in this run. The missing action is to provide an isolated game session, then execute the above checkpoints on disposable copies. No speculative launch flag, original-folder replacement or WGS write-back is prescribed.


## Independent review follow-up

SQLite INTEGER affinity still permits text. The reader rejects unsupported/non-integer Merlin states and missing/blank/non-ASCII/duplicate normalized keys as UNAVAILABLE without echoing values. Seven regressions reproduced and corrected these boundaries and catalogs without Butterfly entries. The final probe suite has 12 cases, including a synthetic private-text sentinel that must never appear in JSON output.

Final full Python suite: 198 passed on Python 3.12 after the independent review fixes. The regression fixture commits its mutated in-memory SQLite image before serialization; a temporary pre-validation source copy reproduced all five unsupported-row failures, and the final reader rejects them without echoing text.
