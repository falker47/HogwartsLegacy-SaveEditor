# Credits and provenance

## Project integration

**falker47** — Windows desktop manager, save discovery/backup workflow, PyWebView integration, packaging and project maintenance.

**Hawk-on** — code-quality refactoring and improvements to the embedded editor integration recorded in this repository's development history.

## hlsaves / hlsavetool

- Upstream project: `gx570s/hlsavetool`
- Original author credited upstream: **Katt**
- Purpose: compress/decompress the SQLite databases stored in Hogwarts Legacy GVAS save files
- License: **MIT** in the upstream source repository
- Nexus Mods page: mod #1983

The upstream MIT notice applies to hlsavetool itself. It is a separate component from this repository's original integration code.

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
