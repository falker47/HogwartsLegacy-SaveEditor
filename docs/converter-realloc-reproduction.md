# Native converter: synthetic round-trip failure and proposed source patches

## Observed behavior

The pinned converter (SHA256 `bdf28ae18dc5ecf049af37ca863085851f2cd0f5b22895f9637c5820c8d0f70e`) compressed a small valid synthetic DB1/DB2 GVAS file, then rejected its own result on decompression because DB1 no longer began with the SQLite signature. The UI reported a conversion failure. The editor's existing verification prevented publication: the disposable target and backup remained byte-identical.

The 25 independently edited copies of game-generated saves passed the same native pipeline. Their success does not establish safety for all allocations or inputs. The synthetic failure must remain recorded.

## Source finding and proposed change

The [pinned upstream compress() implementation](https://github.com/gx570s/hlsavetool/blob/1bab30e3f62a23e8687c2d4995356fd48949dd05/src/oodle.c#L86-L93) calls `realloc(data->value, new_size)`, then uses the old `data->value` as the source of `memmove`. If realloc moved the block, that old pointer is invalid. The returned pointer retains the original bytes; using `new_value` as both the allocation base and move source fixes this source defect and handles overlap.

[HL-02C-realloc-source.patch](../third_party/hlsavetool/HL-02C-realloc-source.patch) changes only that source pointer. It applies to the pinned upstream version after the existing HL-02A patch (which changes a different file). An independent source review confirmed the defect and the minimal correction.

This source finding is proven; attributing the observed runtime failure exclusively to it remains an inference because the allocator move was not instrumented in the integrated converter. The original MSVC 19.29 toolchain was unavailable in the earlier local environment. A **temporary** patched executable has since been compiled in GitHub Actions using MSVC 19.44, but it was not validated with Oodle, promoted, shipped, or checked for binary identity with the older compiler. The pinned archive, installer hashes and application converter remain unchanged.

## Capacity hardening candidate and native compilation — 26 October 2026

[HL-02D-output-capacity.patch](../third_party/hlsavetool/HL-02D-output-capacity.patch) applies after HL-02A and HL-02C. It adds an overflow-checked grow-on-demand buffer for each UpkOodle header and compressed payload, validates Oodle-reported lengths, uses a non-wrapping chunk position counter, and rejects serialized results too large for UArrayProperty. It changes only source code and adds a small native helper header; it does not include Oodle or any user data.

[Native Windows build and capacity test](https://github.com/falker47/HogwartsLegacy-SaveEditor/actions/runs/40348465659): **PASS**, using Visual Studio 2022/MSVC 19.44.35229.0 on runner windows-2022. The patched full converter compiled, and [native_chunk_capacity.c](../tests/native_chunk_capacity.c) exercised reallocation growth, preservation of existing bytes, overflow rejection, and no-op reservations. The same helper had previously passed standalone GCC and Clang checks. [General CI](https://github.com/falker47/HogwartsLegacy-SaveEditor/actions/runs/40348465895): **PASS** at commit `6e76946`. This is source compilation and a helper-unit test, **not** an Oodle-backed save round trip.

The pinned converter executable has **not** been changed. In particular, its synthetic DB1/DB2 failure remains the latest native end-to-end result; a corrected converter has not yet been exercised against Oodle or game-generated save copies.

## Reproduce without personal saves

With the repository Python test dependencies available and the already authorized Oodle runtime beside the converter:

```powershell
py -3.12 scripts/reproduce_converter_realloc.py --converter C:\\QA\\runtime\\hlsaves.exe --out-dir temp/realloc-repro-01
```

The output directory must not exist. The script verifies the converter hash before executing it, generates two valid synthetic SQLite images, compresses and decompresses to new files, and writes a diagnostic `result.json`. Exit 0 means an exact round trip; exit 1 records a native failure/mismatch. Realloc placement is allocator-dependent, so one successful run cannot disprove the source defect. The script does not access personal saves, configuration, WGS or cloud storage, and never installs/copies/downloads a DLL.

## Required before binary promotion

- Rebuild baseline and corrected source with a recorded toolchain, preserving MIT attribution and HL-02A DB2/tail behavior; independently reproduce the resulting bytes.
- Instrument or force a moving realloc to demonstrate that the source regression fails before and passes after the change.
- Exercise the standalone synthetic case repeatedly, the game-generated copy corpus, DB1/DB2, missing/empty DB2, chunk boundaries and opaque-byte invariants.
- Exercise poorly compressible data and compressed chunks larger than the original buffer. The new HL-02D candidate bounds growth, but this has only been proven by a native helper-unit test and source compilation; full Oodle integration, error-path checks and boundary round trips are still required.
- Re-run installer/hash tamper tests, native exact round trips, publication/concurrency/recovery tests and Windows release smoke. Update provenance, checksums and vendored artifact only after those gates pass.

No new converter binary or runtime is committed by this PR. This is a reproducible investigation and proposed source correction, not a claim that the candidate converter has been fixed.
