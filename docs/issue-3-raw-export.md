# Issue #3: raw database export verification

Scope: only Player > Save File > Download Database 1 / Download Database 2.
Refs #3. No release, merge, game data, Oodle DLL, or unrelated feature changes.

## Baseline and diagnosis

On 2026-09-26, a fresh clone and `git fetch origin main` confirmed
`8673257f3f8bb058df9f4b1dc0b549719aba26d4` (the supplied baseline).
The working tree was clean; no AGENTS.md was present in the checkout or its
ancestors. Issue #3 was open, with no open PRs. Baseline CI
[35730090926](https://github.com/falker47/HogwartsLegacy-SaveEditor/actions/runs/35730090926)
had successful python-tests, editor-build and release-smoke jobs.
Branch: `fix/issue-3-raw-database-download`.

Both the external bridge and inline fallback intercepted every anchor carrying
`download`, including `sqldb1.sqlite` and `sqldb2.sqlite`. They passed its blob to
`EditorApi.save_edited_file`, which wrote `.edited`, invoked `hlsaves -c` against
the original save and emitted the write-back status. The app consumes that status
as “Save updated”. MIME type cannot distinguish these downloads from full saves.

Before changing production code, the Node harness executed both actual bridges,
the Vue download handlers and their programmatic anchor clicks. Two distinct
valid SQLite databases were extracted through the real SaveGameData and
SaveGameManager. Both tests failed with:

```text
raw SQLite must never be sent to save_edited_file / hlsaves
expected: 0
actual: 2
Baseline evidence: both SQLite payloads reached real save_edited_file,
wrote loaded.edited, and invoked mocked hlsaves -c against original.sav.
```

This is a behavioral RED, not a missing-method/import failure. The test checks
the exact SQLite payloads, real `.edited` bytes and mocked subprocess arguments
before the failing assertion. After the patch the same cases pass.
This demonstrates H1; it does **not** demonstrate the reported cmd flash or
Windows GUI error, nor run the actual compressor.

## Change and safety contract

- Exact existing download names form the routing contract: `sqldb1.sqlite` and
  `sqldb2.sqlite` go to `export_database`; only `hlsave.sav` and
  `hlcustomsave.sav` go to write-back. Unknown names fail without recompression.
- Raw export validates strict base64 and the SQLite signature, then uses the
  editor window's native Save dialog. It writes bytes unchanged, with a `.sqlite`
  filename. Existing destinations are deliberately refused: choose a new filename
  for repeated exports. Exclusive creation also protects hard links and backups.
- Original/decompressed paths are rejected explicitly. No raw export writes
  `.edited`, calls hlsaves, emits a write-back callback or closes the window.
- Cancellation is distinct from success. Dialog, decoding and write errors are
  returned to the bridge; partial new files are removed after write failure.
  Fetch/FileReader errors and aborts remove the blocking overlay. A later export
  remains usable in the same session.
- Both bridge copies are patched and executed by the regression suite. Launch
  tests also exercise missing/unreadable external scripts and window binding.

The installed Python 3.12 environment has **pywebview 5.4**, inside the project's
`>=4.0.0,<6.0.0` requirement. Its actual `Window.create_file_dialog` signature and
WinForms implementation were inspected: `webview.SAVE_DIALOG` is 30,
`save_filename` and `file_types` are supported, and Windows returns a **string**.
Other backends/documentation return a sequence; both are covered. The current
[official API reference](https://pywebview.flowrl.com/api/#window-create-file-dialog)
describes a newer enum spelling; this patch uses the installed version's API.
The [4.0.1 source](https://github.com/r0x0r/pywebview/blob/4.0.1/webview/__init__.py)
also defines `SAVE_DIALOG`. No dependency versions were changed.

The frontend producers, parser, `getDatabase()` and `generateSaveFile()` are
unchanged. Tests modify the in-memory SQL database and confirm that raw export
still returns the originally loaded bytes. Normal/custom save tests execute the
real generation path but mock hlsaves: they are **not** compression round trips.

## Automated checks

Local environment: Windows 10.0.26200, PowerShell 7.6.5, Git 2.45.1.windows.1,
Node 22.16.0, npm 10.9.2, Python 3.14.3 / pytest 9.0.2. Python 3.12.10 was also
used to inspect installed pywebview; CI uses Python 3.12 and Node 20.

| Directory | Command | Baseline | Patch |
| --- | --- | --- | --- |
| repository root | `python -m pytest -q` | PASS, 10 tests | PASS, 44 tests |
| repository root | `python -m pytest -q -p no:cacheprovider` | not needed | PASS, 44 tests, no cache warning |
| `HLSE-src` | `npm ci --cache .cache/npm --no-audit --no-fund` | PASS, 224 packages from unchanged lockfile | same installation used |
| `HLSE-src` | `node --test tests/editor-downloads.test.cjs` | expected FAIL, 2 routing regressions | PASS |
| `HLSE-src` | `npm test` | script added by this patch | PASS, 30 tests |
| `HLSE-src` | `npm run build` | PASS, 492 modules | PASS, 492 modules |
| `HLSE-src` | `npm run lint` | FAIL, 5 errors / 501 warnings | identical FAIL, no new diagnostics |
| repository root | `node --check assets/editor_bridge.js` | not needed | PASS |
| repository root | `node --check HLSE-src/tests/editor-downloads.test.cjs` | not applicable | PASS |
| repository root | `git diff --check` | clean tree | PASS |

Lint errors are pre-existing: `collectionsPage.vue:14` (`curly`),
`resources/saveGameDB.ts:1` (`ban-ts-comment`) and `vue-shim.d.ts:2-4` (three
missing semicolons). Baseline/final lint output compares equal. No lint rule was
disabled, no global fix was run, and no existing CI check was weakened.

Environment retries: sandbox network access initially blocked clone/npm ci;
esbuild was blocked reading ancestor directories; pytest's default temp root
was inaccessible. Authorized retries outside the sandbox succeeded. The standard
pytest run reported one local cache permission warning; the no-cache run passed
without warnings. These are distinct from the persistent baseline lint failures.

CI retains the full headless pytest job. The existing Node editor-build job now
installs Python 3.12 and runs `npm test` before the build. The test bridge crosses
into real Python file I/O using a stdlib JSON harness; it needs no GUI packages.
The existing Windows release-smoke remains unchanged. Its eventual result must
be recorded on the final PR commit, separately from these local observations.

The runtime HTML was not manually edited or replaced: no frontend source changed.
Its content equals the canonical build after normalizing CRLF/LF (normalized
SHA-256 `373b2d0df49afad5b9506a9614b330d0389ca5a5cca8e1aed473d1b45dca9d9d`).
The canonical build still produces `HLSE-src/dist/client/index.html` and
`build_release.bat` retains its existing copy to `assets/HLSGE.html`.

## Coverage and evidence boundaries

- Both DB identities and suggested filenames, exact output bytes and lengths,
  SHA-256 equality, `PRAGMA integrity_check = ok`, distinct contents/no swapping.
  A local Python/SQLite sample produced 16,384 bytes for each: DB1 SHA-256
  `f01c809a45c011e33e28fb7037e76ab29e2e2a1b643fbb66678fea39ad3858b9`, DB2
  `5481f1a421ebbb15443fea4e317443ca5daa055ea6aa843a700c07e5c91e1ed4`.
  Tests compare against freshly generated fixtures, not hard-coded hashes across
  different SQLite versions.
- Original, decompressed and backup sentinel contents unchanged; no `.edited`,
  subprocess, write-back callback, “Save Updated” or auto-close on raw export.
- External and actual missing-file fallback execution; unreadable-file fallback
  and startup binding through Python launch tests.
- General fileHandler download, Save File page download, custom uploaded DBs;
  successful and failing mocked compression with existing status/close behavior.
- Cancel, malformed base64/payload, dialog/write failure (including partial write),
  fetch/read/abort/API rejection, unknown downloads and subsequent exports.

The fixtures are generated locally in temporary directories. Their minimal
GVAS-shaped container exists solely to run the real extraction/generation code;
it is **synthetic**, not a valid in-game compatibility fixture. No personal saves,
game launch, proprietary binaries or secrets are used or committed.

## Residual manual gate — NOT EXECUTED

Native Windows dialog interaction and an authorized real-save flow have not
been executed. Keep the PR Draft until this gate is accepted. Local
`build_release.bat`, in-game verification and release certification are SKIPPED.

Minimum repeatable check:

1. Work only on a copy of an authorized save; record hashes of that original copy,
   its decompressed input and backup. Independently extract/reference the DB1/DB2
   bytes from that decompressed input before making pending editor changes.
2. Load the copy, open Player > Save File, export DB1 and DB2 to new filenames in
   a temporary folder. Confirm the native suggested names, exact bytes/hashes
   against those references and `PRAGMA integrity_check = ok` for each file.
3. Confirm unchanged save/decompressed/backup hashes, no raw `.edited`, no
   “Save Updated”, and that the editor remains usable. Repeat after cancelling
   the dialog and after an export error (for example an existing destination).
4. On a separate sacrificial copy, check the normal complete-save operation and
   its expected success/close behavior. This is a separate check from raw export.

Review/acceptance remains separate. No merge, auto-merge, tag, release, issue
closure/comment, Trello/PersonalContext change, or subsequent task is authorized
by this checkpoint.
