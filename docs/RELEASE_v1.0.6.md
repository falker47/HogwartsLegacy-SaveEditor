# Hogwarts Legacy Save Editor & Manager v1.0.6

v1.0.6 is a recovery and compatibility release focused on the unresolved Nexus-reported editor paths, save identification, and Game Pass support.

## Highlights

- Restores guarded **Experience** editing with validated bounds and progression safeguards.
- Restores **Talent Points** editing with the vanilla `learned + unspent <= 36` invariant.
- Restores verified **Wand Handles** and **Revelio Pages** unlock/lock operations.
- Restores **Galleons** editing and exposes **Wiggenweld / HealthPotionStorage** in Combat Resources.
- Keeps Player Apply atomic and limited to fields that were actually changed.
- Adds a profile-aware, in-game-style save browser with character labels, manual/autosave type, playtime, verified locations, internal game time, and technical filenames.
- Adds **Export Game Pass Saves**: recognized WGS payloads are copied byte-for-byte into ordinary editable/migration `.sav` files.

## Game Pass safety

Game Pass/WGS saves are **not edited in place**. The exporter does not write WGS payloads, indexes, container metadata, or Xbox cloud state. Exported saves are ordinary copies for editing/migration only.

The generic “no saves found” report remains a separate case unless reproduced outside the validated Game Pass path.

## Validation

Release-relevant paths received focused real-save and in-game validation, including progression safeguards, Wand Handles, Revelio Pages, Galleons, Wiggenweld, Player Reset, validation rollback, final save/reload, the new save-browser UI, and the real Game Pass detection/export flow.

GitHub Actions also validates the Python suite, embedded-editor tests/build, and the full Windows release-smoke package.

## Third-party note

The proprietary Oodle DLL is **not bundled**. Existing discovery/fallback behavior and third-party notices remain in effect.
