# Game Pass safe export

This port starts at `bbb27f6b95d7e86e731635626ccd4747df090a02` and uses PR #14
(`446e91dacbf3f12b8322d0c6bdd6ace34438c273`) only as behavioral evidence.
The current SaveBrowser, SaveEntry, named profiles, cached background discovery,
metadata presentation, and exact selected edit source remain in use.

## Scope and safety

- Detect only `%LOCALAPPDATA%/Packages/WarnerBros.Interactive.PHX_ktmk1xygcecda/SystemAppData/wgs`.
- Resolve exactly one immediate user directory with a regular `containers.index` marker.
- Read immediate container payloads only. Skip links/reparse points, container metadata,
  empty/unreadable files, and files larger than 50 MiB. Actual reads are bounded too.
- Require a complete ASCII `HL-XX-XX` identity. Repeated identical tags are one identity;
  multiple identities in one payload or different bytes claiming one identity stop export.
  Identical duplicate payloads are deduplicated with SHA-256.
- Refuse destinations within the source WGS tree or other recognized WGS storage.
- Preflight all target names; create each `.sav` exclusively, never overwrite. Re-read
  and verify payload hashes before writing. On failure remove only newly created outputs,
  including the partially written current file. Track file identities to preserve outputs
  replaced by another process; report any cleanup failures explicitly.
- Export runs on a worker; main-thread completion uses `_set_save_directory` and the
  existing catalog refresh. The destination becomes the persisted manual save folder.
- Ordinary editing and database export retain their existing WGS write prohibitions.

Close the game before exporting. Export does not lock Xbox cloud storage or certify a
cloud snapshot. This is a conservative recognizer, not a WGS protocol implementation.
Unrecognized formats require investigation; users must not rename or replace WGS files.

## Acceptance

Automated fixtures are generated synthetic metadata and bytes, never real user saves.
Tests cover root/user detection, ambiguous users/tags/payloads, bounded reads, duplicate
handling, byte identity, unchanged source bytes/mtime, existing-target refusal, partial
write rollback, concurrent target creation, source changes, links, cancellation, worker
completion, diagnostics, and integration with current character/profile save cards.
Existing Steam/Epic, PR #16 recovery, and PR #17 save-browser tests remain required.

Real Game Pass user-flow validation: **PASS — 29 September 2026**.
An authorized real Game Pass installation confirmed the detection/export flow works as
intended after the automated/CI gate. This validates the supported safe-export path; it
does not add or imply WGS/cloud write-back, which remains outside scope.

The generic Nexus "no saves found" report is not claimed fixed without a reproducible
case. If no ordinary saves or WGS root are detected, the UI explains that no supported
folder was auto-detected and Browse remains available.
