# Credits and provenance

## Project integration

**falker47** — Windows desktop manager, save discovery/backup workflow, PyWebView integration, packaging and project maintenance.

**Hawk-on** — code-quality refactoring and improvements to the embedded editor integration recorded in this repository's development history.

## hlsaves / hlsavetool

- Upstream project: `gx570s/hlsavetool`
- Original author credited upstream: **Katt**
- Purpose: compress/decompress the SQLite databases stored in Hogwarts Legacy GVAS save files
- License: **MIT** in the upstream source repository
- Parent project: `topche-katt/hlsavetool`
- Pinned project dependency: **v2.0.1 + HL-02A** (downstream package `2.0.1-hl02a.1`)
- Nexus Mods page: mod #1983

The repository vendors the reproducible converter ZIP with a minimal local DB2 tail-parsing patch. Setup/build installs it offline and verifies both ZIP and executable hashes. See [public patch and provenance](third_party/hlsavetool/PROVENANCE.md). The upstream MIT license and **Copyright (c) 2024 Katt** remain at `third_party/hlsavetool-LICENSE.txt`; the separate Oodle DLL is not distributed.

## HLSGE / Hogwarts Legacy Save Game Editor

- Upstream distribution: Nexus Mods mod #77
- Purpose: browser-based save database editor
- Local integration: built into a single HTML file and hosted inside PyWebView
- Local project history also contains editor fixes/customizations and credits **ekaomk** in earlier documentation

HLSGE's upstream permissions are separate from this repository's MIT license. No statement in this repository should be read as relicensing the upstream editor. See `THIRD_PARTY_NOTICES.md`.

## Libraries

The desktop application also uses:

- CustomTkinter
- pywebview
- tkinterdnd2

The embedded editor uses the JavaScript dependencies declared in `HLSE-src/package.json`.

Each dependency remains under its own upstream license.

## Project license scope

The root `LICENSE` covers original code authored for this repository unless a file or third-party notice states otherwise. It does not supersede the licenses, permissions, copyrights, or trademarks of external components.
