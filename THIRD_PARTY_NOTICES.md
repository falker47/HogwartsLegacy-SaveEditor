# Third-party notices

This file documents provenance and license boundaries for external components used by Hogwarts Legacy Save Editor & Manager.

## 1. hlsaves / hlsavetool

**Upstream:** https://github.com/gx570s/hlsavetool  
**Purpose:** compression/decompression of Hogwarts Legacy save databases  
**Pinned release:** v2.0.1 (2026-04-30)  
**Pinned release archive SHA-256:** `a5733229c767f451d0b2612df88af2823e84e769b482d9b0eebe7f6fc09472ed`  
**Upstream license:** MIT  
**Upstream copyright notice:** Copyright (c) 2024 Katt

The executable is not committed to this repository. `scripts/fetch_hlsaves.ps1` downloads the pinned upstream GitHub release archive, verifies the archive SHA-256, locates `hlsaves.exe`, and installs it into `assets/` for local use or packaging.

The upstream MIT notice is preserved at `third_party/hlsavetool-LICENSE.txt` and is copied into release packages.

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

The application prefers locating a compatible copy from the user's installed games. Current v1.0.4 code also offers a hash-pinned third-party fallback URL hosted in the `new-world-tools/go-oodle` GitHub release assets. That hosting location does not make the DLL part of the MIT-licensed codebase or an official distribution channel.

## 4. Hogwarts Legacy and related marks

Hogwarts Legacy and related names, assets and trademarks belong to their respective owners. This project is unofficial and unaffiliated.

## 5. Dependency licenses

Python and JavaScript dependencies retain their own upstream licenses. Their presence in dependency manifests does not place them under this repository's MIT license.
