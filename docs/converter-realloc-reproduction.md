# Native converter: synthetic round-trip failure and proposed source patch

## Observed behavior

The pinned converter (SHA256 `bdf28ae18dc5ecf049af37ca863085851f2cd0f5b22895f9637c5820c8d0f70e`) compressed a small valid synthetic DB1/DB2 GVAS file, then rejected its own result on decompression because DB1 no longer began with the SQLite signature. The UI reported a conversion failure. The editor's existing verification prevented publication: the disposable target and backup remained byte-identical.

The 25 independently edited copies of game-generated saves passed the same native pipeline. Their success does not establish safety for all allocations or inputs. The synthetic failure must remain recorded.

## Source finding and proposed change

The [pinned upstream compress() implementation](https://github.com/gx570s/hlsavetool/blob/1bab30e3f62a23e8687c2d4995356fd48949dd05/src/oodle.c#L86-L93) calls `realloc(data->value, new_size)`, then uses the old `data->value` as the source of `memmove`. If realloc moved the block, that old pointer is invalid. The returned pointer retains the original bytes; using `new_value` as both the allocation base and move source fixes this source defect and handles overlap.

[HL-02C-realloc-source.patch](../third_party/hlsavetool/HL-02C-realloc-source.patch) changes only that source pointer. It applies to the pinned upstream version after the existing HL-02A patch (which changes a different file). An independent source review confirmed the defect and the minimal correction.

This source finding is proven; attributing the observed runtime failure exclusively to it remains an inference because the allocator move was not instrumented. The replacement binary has **not** been built or validated. The exact recorded MSVC toolchain was not available at its recorded path and no compiler was found in the available PATH. No compiler was installed. The pinned archive, installer hashes and application converter remain unchanged.

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
- Exercise poorly compressible data. Source review also identified a separate inherited capacity concern: `result_data` is allocated to the original DB size but receives chunk headers plus compressed data without a capacity check. The one-line realloc patch does not address that concern; validate/fix capacity and all associated failure paths before promoting a new converter.
- Re-run installer/hash tamper tests, native exact round trips, publication/concurrency/recovery tests and Windows release smoke. Update provenance, checksums and vendored artifact only after those gates pass.

No new converter binary or runtime is committed by this PR. This is a reproducible investigation and proposed source correction, not a claim that the candidate converter has been fixed.
