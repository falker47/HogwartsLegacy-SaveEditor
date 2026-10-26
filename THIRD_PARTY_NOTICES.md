# Third-party notices

This file documents provenance and license boundaries for external components used by Hogwarts Legacy Save Editor & Manager.

## 1. hlsaves / hlsavetool

- **Upstream:** https://github.com/gx570s/hlsavetool
- **Parent project:** https://github.com/topche-katt/hlsavetool
- **Purpose:** compression/decompression of Hogwarts Legacy save databases
- **Baseline:** v2.0.1, with local HL-02A DB2 tail, HL-02C realloc-source and HL-02D output-capacity patches
- **Vendored package:** 2.0.1-hl02acd.1
- **ZIP SHA-256:** `d3aeb8f6c8a8faab3c67041f0265a06446cdc71e9abc876b3a632293ea3f77fc`
- **EXE SHA-256:** `4080b409c125c29a3b977ed42160e36fb422fe0eaaa7f0c5d9419737a81cd3bb`
- **Upstream license:** MIT
- **Upstream copyright notice:** Copyright (c) 2024 Katt

The executable is stored inside the reproducible ZIP under `third_party/hlsavetool/`. The standalone `assets/hlsaves.exe` remains ignored. `scripts/fetch_hlsaves.ps1` installs from this local archive without network access, verifies the archive and extracted executable, and verifies the final copied executable.

The public [patch and provenance](third_party/hlsavetool/PROVENANCE.md) record the upstream baseline, patch identity, build toolchain and validation results. The converter remains third-party code credited to Katt.

The canonical MIT notice stays at `third_party/hlsavetool-LICENSE.txt` and is copied into release packages together with the patch/provenance. The Oodle DLL is separate and is not included.

## 2. HLSGE / Hogwarts Legacy Save Game Editor

**Upstream project page:** https://www.nexusmods.com/hogwartslegacy/mods/77  
**Purpose:** web-based save database editor

This repository contains an embedded build and source/customizations derived from HLSGE. The upstream project page applies permissions that are distinct from this repository's root MIT license.

Accordingly:

- the root MIT license must not be interpreted as relicensing HLSGE;
- attribution to the upstream editor must be preserved;
- redistribution/modification rights for HLSGE must be established from the upstream author/permissions independently of this repository's license.

The repository history and connected email search performed during the September 2026 GPR audit did not surface a standalone permission grant that can be treated as authoritative evidence. If an external permission grant exists, it should be preserved in durable project records and this notice updated accordingly.

## 3. oo2core_9_win64.dll

**Component:** Oodle runtime DLL  
**Vendor technology:** Epic Games / RAD Game Tools

The DLL is proprietary third-party software. It is intentionally ignored by Git and excluded from release packaging.

The application prefers locating a compatible copy from the user's installed games. Current v1.0.6 code also offers a hash-pinned third-party fallback URL hosted in the `new-world-tools/go-oodle` GitHub release assets. That hosting location does not make the DLL part of the MIT-licensed codebase or an official distribution channel.

## 4. Hogwarts Legacy and related marks

Hogwarts Legacy and related names, assets and trademarks belong to their respective owners. This project is unofficial and unaffiliated.

## 5. Dependency licenses

Python and JavaScript dependencies retain their own upstream licenses. Their presence in dependency manifests does not place them under this repository's MIT license.
