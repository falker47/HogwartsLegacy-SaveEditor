# Hogwarts Legacy Save Editor & Manager

![Banner](banner_rectangular.png)

A Windows desktop manager that connects three pieces of the Hogwarts Legacy save-editing workflow: save discovery and backups, `hlsaves` compression/decompression, and the HLSGE web editor inside a local PyWebView window.

**Latest packaged release:** v1.0.4

## What this project adds

- automatic discovery of Hogwarts Legacy save folders, with manual override;
- persistent local configuration for the selected save directory;
- automatic backups before an edited save is written back;
- an integrated PyWebView workflow, so the editor opens next to the save manager instead of requiring manual upload/download steps;
- discovery of the required Oodle DLL from common Steam/Epic installations, plus an explicit user-triggered wider search;
- a small Python bridge that intercepts the editor's download and recompresses the edited database into the original save.

This repository is an integration project. It does **not** claim authorship of the external save-format/editor components listed under [Third-party components](#third-party-components).

## Architecture

```text
Hogwarts Legacy .sav
        |
        v
  hlsaves.exe
(decompress / recompress)
        |
        v
 temporary database
        |
        v
 HLSGE single-file editor
        |
        v
 assets/editor_bridge.js
        |
        v
 Python / PyWebView bridge
        |
        v
 original save + backup
```

The desktop layer is Python + CustomTkinter. The embedded editor source lives under `HLSE-src/` and is built with Vue/Vite into a single HTML file consumed by PyWebView.

## Requirements

- Windows
- Python 3.12+ when running from source
- Node.js 20+ when rebuilding the embedded editor
- `oo2core_9_win64.dll`, normally obtainable from an installed game that ships the compatible Oodle library

### Oodle DLL handling

The application first checks common Hogwarts Legacy Steam/Epic locations. If those checks fail, the user may explicitly start a broader local search or select the DLL manually.

The current v1.0.4 code also contains a hash-pinned fallback download from the third-party `new-world-tools/go-oodle` release assets. That source is **not an official Epic Games distribution channel**, and the DLL itself is not covered by this repository's MIT license. Prefer using the copy from your own installed game when available.

The DLL is intentionally excluded from this repository and from release packaging.

## Installation

### Packaged release

1. Download the latest ZIP from [GitHub Releases](../../releases/latest).
2. Extract it to a writable folder.
3. Run `HogwartsLegacy-SaveEditor.exe`.
4. Let the app locate `oo2core_9_win64.dll`, or provide it manually if needed.

### Run from source

```powershell
git clone https://github.com/falker47/HogwartsLegacy-SaveEditor.git
cd HogwartsLegacy-SaveEditor
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\fetch_hlsaves.ps1
python -m pip install -r requirements.txt
python main.py
```

`fetch_hlsaves.ps1` acquires the pinned upstream hlsavetool v2.0.1 release and verifies its published archive SHA-256 before installing `assets/hlsaves.exe`. The generated executable stays ignored by Git.

## Usage

1. Launch the manager.
2. Select the detected save folder or browse to it manually.
3. Select a save and choose **Edit Save File**.
4. Make changes in the integrated editor.
5. Use the editor's **Download** action.
6. The bridge writes the edited database and asks `hlsaves` to recompress it into the original save path.

Backups are stored in a `Backups` directory under the selected save folder. Keep an independent backup before experimenting with save editors.

## Development and verification

### Python tests

```bash
python -m pip install pytest
pytest -q
```

The current unit suite covers utility-level save-name parsing and file-size formatting. It does **not** constitute end-to-end save-integrity certification.

### Embedded editor build

```bash
cd HLSE-src
npm ci
npm run build
```

The production Vite build emits a single-file editor at `HLSE-src/dist/client/index.html`.

### Release build

On Windows:

```bat
build_release.bat
```

The release builder acquires the pinned hlsavetool release with SHA-256 verification, rebuilds the embedded editor, runs the Python tests, builds the executable with PyInstaller, and assembles the distributable while deliberately excluding the Oodle DLL.

GitHub Actions checks Python tests and the frontend production build on Linux, plus a full Windows release smoke build that verifies the expected package contents and confirms that the Oodle DLL is absent.

## Repository map

```text
.
├── main.py
├── src/                    # desktop manager and PyWebView integration
├── assets/
│   ├── HLSGE.html          # built embedded editor artifact
│   └── editor_bridge.js
├── scripts/
│   └── fetch_hlsaves.ps1   # verified acquisition of upstream hlsavetool
├── third_party/
│   └── hlsavetool-LICENSE.txt
├── HLSE-src/               # embedded editor source/customizations
├── tests/
├── docs/
├── build_release.bat
└── CREDITS.md
```

## Third-party components

This project depends on components with their own provenance and terms:

- **hlsaves / hlsavetool** — compression/decompression utility by Katt; upstream source is MIT-licensed. The project pins v2.0.1 and verifies the release archive before packaging it.
- **HLSGE / Hogwarts Legacy Save Game Editor** — embedded web editor derived from the Nexus Mods project; its upstream permissions are separate from this repository's license.
- **oo2core_9_win64.dll** — proprietary Oodle runtime component; not distributed by this repository.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [CREDITS.md](CREDITS.md) for the scope of attribution and licensing.

## Release history

- **v1.0.4** — revert/unlock fixes and the current packaged release.
- **v1.0.3** — configuration persistence, non-blocking DLL discovery flow, refactoring and editor enhancements.
- **v1.0.2** — direct local editor loading instead of the previous local-server path.
- **v1.0.1** — hash verification for the optional DLL download.
- **v1.0.0** — initial public release.

## License

The original desktop manager, integration code, and other code authored for this repository are licensed under the [MIT License](LICENSE).

That license does **not** automatically relicense bundled or derived third-party material. HLSGE, `hlsaves`, the Oodle DLL, game data, trademarks, and other external assets remain subject to their respective upstream terms. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Disclaimer

This is an unofficial fan-made utility and is not affiliated with Avalanche Software, Warner Bros. Games, Epic Games, or the authors of the third-party tools it integrates. Save editing can corrupt progress; keep backups and test changes carefully.
