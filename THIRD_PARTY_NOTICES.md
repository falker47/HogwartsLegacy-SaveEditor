# Third-party notices

This file documents provenance and license boundaries for external components used by Hogwarts Legacy Save Editor & Manager.

## 1. hlsaves / hlsavetool

- **Upstream:** https://github.com/gx570s/hlsavetool
- **Parent project:** https://github.com/topche-katt/hlsavetool
- **Purpose:** compression/decompression of Hogwarts Legacy save databases
- **Baseline:** v2.0.1, with the minimal local HL-02A DB2 tail-parsing patch
- **Vendored package:** 2.0.1-hl02a.1
- **ZIP SHA-256:** `eeedcc913d1ea916e9edc6b599002bac7823a9989050b79851b5f9f02c0b7a75`
- **EXE SHA-256:** `bdf28ae18dc5ecf049af37ca863085851f2cd0f5b22895f9637c5820c8d0f70e`
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

The application prefers locating a compatible copy from the user's installed games. Current v1.0.5 code also offers a hash-pinned third-party fallback URL hosted in the `new-world-tools/go-oodle` GitHub release assets. That hosting location does not make the DLL part of the MIT-licensed codebase or an official distribution channel.

## 4. Hogwarts Legacy and related marks

Hogwarts Legacy and related names, assets and trademarks belong to their respective owners. This project is unofficial and unaffiliated.

## 5. Dependency licenses

Python and JavaScript dependencies retain their own upstream licenses. Their presence in dependency manifests does not place them under this repository's MIT license.
