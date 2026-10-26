# Current candidate: hlsavetool 2.0.1-hl02acd.1

Upstream MIT code: gx570s/hlsavetool at `1bab30e3f62a23e8687c2d4995356fd48949dd05`, credited to Katt.
Apply HL-02A (DB2 tail), HL-02C (realloc source) and HL-02D (output capacity), in order.
The current ZIP includes the exact patched `source/src` and `source/headers`, all three patches, license,
SOURCE.json with per-file hashes, and build-gcc.ps1. The older package below is retained only for history.

- ZIP: `HLSaveToolv2.0.1-hl02acd.1.zip`, SHA256 `d3aeb8f6c8a8faab3c67041f0265a06446cdc71e9abc876b3a632293ea3f77fc`.
- EXE: 161449 bytes, SHA256 `4080b409c125c29a3b977ed42160e36fb422fe0eaaa7f0c5d9419737a81cd3bb`.
- Toolchain: existing MSYS2 UCRT64 GCC 13.1.0 Rev6; `-O2 -static -Wl,--no-insert-timestamp`.
- Rebuilds using both relative and absolute source paths reproduced identical executable bytes.
- Windows system UCRT is required; no MinGW runtime DLL dependency. Oodle is loaded separately.
- 26 October 2026: actual local Oodle passed 55 exact round trips across 11 synthetic cases, five cycles
  each; valid SQLite output-expansion case (5125 to 5137 bytes), entropy up to 6.3 MB, DB1/DB2,
  DB2 absent, opaque inter-image/tail data. A separate test-only forced-moving-realloc executable
  passed the same 55 cycles. Native capacity unit tests pass.
- Production JS manager/generator plus Python verified publication passed on 25 new game-save copies;
  exactly one chosen Gear stat changed, all remaining DB1/DB2/opaque data preserved, 27 original hashes unchanged.
- No gameplay acceptance is implied. Local runtime provenance was confirmed by the user.

Neither ZIP nor release includes Oodle or user save data. Tests requiring Oodle are local opt-in checks;
public CI compiles native source and verifies the helper without downloading proprietary software.

---

# Historical package: v2.0.1 + HL-02A

This is a third-party MIT component, originally credited to **Katt**, with a minimal local DB2 tail fix. It is not original converter code authored by falker47. The downstream package label is **2.0.1-hl02a.1**, not an upstream release.

## Source and patch identity

- Upstream used for this baseline: https://github.com/gx570s/hlsavetool
- Parent project: https://github.com/topche-katt/hlsavetool
- Baseline tag: **v2.0.1**
- Baseline commit: `1bab30e3f62a23e8687c2d4995356fd48949dd05`
- Original upstream release archive SHA-256: `a5733229c767f451d0b2612df88af2823e84e769b482d9b0eebe7f6fc09472ed`
- Audited local patched commit: `480059cb237724e8605505e62a4e516a58adbce3` (an identity record; no separate public fork is required)
- Public format-patch: [HL-02A-db2-tail.patch](HL-02A-db2-tail.patch), SHA-256 `465cff7dab7712d1846091fd2e0f71b38445218b7cafb74d8c22da2cf4712a5f`
- Raw diff SHA-256: `637419d05531e72e76f5ca61193d04dd2b0e039fa1e1c557d002d09ea0854a20`

The format-patch includes commit metadata; its raw diff is also included as `candidate.patch` inside the ZIP. Both describe exactly one hunk in `src/hlsaves.c`: **4 insertions, 5 deletions**.

`RawExclusiveImage` has a longer FString name than `RawDatabaseImage`. The original `property2->length + RDI_UPROPERTY_DATA_OFFSET` calculation reuses the fixed offset 65 and starts the tail one byte too early, duplicating the last DB2 payload byte. The fix uses the pointer already advanced by `parse_uproperty`:

```c
tail.address = address2;
tail.size = (size_t)((buffer + buffer_size) - address2);
```

No other hlsavetool source behavior is changed.

## Pinned artifact and reproduction

- Vendored archive: [HLSaveToolv2.0.1-hl02a.1.zip](HLSaveToolv2.0.1-hl02a.1.zip)
- ZIP SHA-256: `eeedcc913d1ea916e9edc6b599002bac7823a9989050b79851b5f9f02c0b7a75`
- Extracted executable: `hlsaves.exe`, **153088 bytes**
- EXE SHA-256: `bdf28ae18dc5ecf049af37ca863085851f2cd0f5b22895f9637c5820c8d0f70e`

The ZIP contains the executable, MIT license, `BUILDING.md`, `SOURCE.json`, build recipe, raw patch and an internal checksum manifest. See those files for the exact commands and compiler component hashes.

Reconstruct the source from the upstream baseline and the public patch; follow the included build recipe. Toolchain: **VS Build Tools 2019 16.11.47**, **MSVC x64 19.29.30159.0**, **linker 14.29.30159.0**, VCToolsVersion **14.29.30133**, **Windows SDK 10.0.19041.0**. The recipe uses `/O2 /MT /DNDEBUG /Brepro` and linker `/Brepro /INCREMENTAL:NO`.

Independent builds from the evidence-matching source and from canonical committed Git blobs reproduced the exact validated HL-02A executable byte for byte. This is reproducibility with the recorded toolchain, not a claim for arbitrary compiler versions.

## Validation

The identical executable passed **DB1+DB2**, **DB2 absent**, **round-trip**, structural/SQLite and tail-invariant checks. Five transformations per fixture preserved the tail without drift. The prior **real E2E HL-02B gate passed**, including full-save on a disposable real-save copy. These results apply to the validated fixture contract, not every possible malformed save.

`scripts/fetch_hlsaves.ps1` installs solely from this vendored ZIP, verifying the archive, extracted EXE and final destination EXE. No network access is needed to acquire this converter. The generated `assets/hlsaves.exe` remains ignored.

## License and distribution boundary

**MIT — Copyright (c) 2024 Katt.** The canonical repository notice remains [hlsavetool-LICENSE.txt](../hlsavetool-LICENSE.txt); preserve it and upstream attribution. Release packages retain that license and this provenance/patch.

**The Oodle DLL is not distributed in this archive or application release.** It is a separate runtime dependency, outside hlsavetool's MIT license. No saves or private validation evidence are included.
