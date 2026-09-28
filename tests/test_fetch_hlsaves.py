"""Exercise the real offline PowerShell installer in disposable repository copies."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_NAME = "HLSaveToolv2.0.1-hl02a.1.zip"
ARCHIVE_SHA256 = "eeedcc913d1ea916e9edc6b599002bac7823a9989050b79851b5f9f02c0b7a75"
EXE_SHA256 = "bdf28ae18dc5ecf049af37ca863085851f2cd0f5b22895f9637c5820c8d0f70e"
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")
pytestmark = pytest.mark.skipif(POWERSHELL is None, reason="PowerShell is required")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def repository(tmp_path):
    repo = tmp_path / "repository with spaces"
    (repo / "scripts").mkdir(parents=True)
    (repo / "third_party" / "hlsavetool").mkdir(parents=True)
    (repo / "test-temp").mkdir()
    shutil.copy2(ROOT / "scripts" / "fetch_hlsaves.ps1", repo / "scripts")
    shutil.copy2(
        ROOT / "third_party" / "hlsavetool" / ARCHIVE_NAME,
        repo / "third_party" / "hlsavetool",
    )
    return repo


def run_installer(repo, destination=None, before_install=""):
    # Calls to network commands fail even if a download is accidentally reintroduced.
    command = """
$ErrorActionPreference = "Stop"
function Invoke-WebRequest { throw "Network access is forbidden in this test" }
function Invoke-RestMethod { throw "Network access is forbidden in this test" }
function Start-BitsTransfer { throw "Network access is forbidden in this test" }
"""
    command += before_install
    command += """
Set-Location -LiteralPath (Split-Path -Parent (Split-Path -Parent $env:HLSAVETOOL_TEST_SCRIPT))
$arguments = @{}
if ($env:HLSAVETOOL_TEST_DESTINATION) {
    $arguments.Destination = $env:HLSAVETOOL_TEST_DESTINATION
}
& $env:HLSAVETOOL_TEST_SCRIPT @arguments
"""
    # Let the selected PowerShell edition discover its own built-in modules.
    env = {key: value for key, value in os.environ.items() if key.upper() != "PSMODULEPATH"}
    env.update(
        TEMP=str(repo / "test-temp"),
        TMP=str(repo / "test-temp"),
        TMPDIR=str(repo / "test-temp"),
        HLSAVETOOL_TEST_SCRIPT=str(repo / "scripts" / "fetch_hlsaves.ps1"),
        HLSAVETOOL_TEST_DESTINATION="" if destination is None else str(destination),
    )
    result = subprocess.run(
        [POWERSHELL, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
         "-Command", command],
        cwd=repo.parent, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=60,
    )
    assert not list((repo / "test-temp").glob("hlsavetool-*")), "Temporary files leaked"
    return result


def change_test_archive(repo, transform):
    """Change only a disposable fixture and its ZIP pin to exercise the EXE gate."""
    archive = repo / "third_party" / "hlsavetool" / ARCHIVE_NAME
    with zipfile.ZipFile(archive) as source:
        members = {name: source.read(name) for name in source.namelist()}
    transform(members)
    with zipfile.ZipFile(archive, "w") as target:
        for name, data in members.items():
            target.writestr(name, data)
    script = repo / "scripts" / "fetch_hlsaves.ps1"
    text = script.read_text(encoding="utf-8")
    assert text.count(ARCHIVE_SHA256) == 1
    # The production installer has no hash override or test-only bypass.
    script.write_text(text.replace(ARCHIVE_SHA256, sha256(archive)), encoding="utf-8")


def existing_destination(repo):
    destination = repo / "existing destination" / "hlsaves.exe"
    destination.parent.mkdir()
    destination.write_bytes(b"existing runtime must survive rejected input")
    return destination


def assert_rejected(result, message):
    assert result.returncode != 0, result.stdout + result.stderr
    assert message in result.stdout + result.stderr
    assert "Installed verified hlsaves.exe" not in result.stdout


@pytest.mark.parametrize("custom_destination", [False, True])
def test_installs_verified_converter_without_network(repository, custom_destination):
    destination = (
        Path("custom output") / "converter.exe" if custom_destination else None
    )
    expected = (
        repository / destination if destination else repository / "assets" / "hlsaves.exe"
    )
    assert sha256(repository / "third_party" / "hlsavetool" / ARCHIVE_NAME) == ARCHIVE_SHA256
    result = run_installer(repository, destination)
    assert result.returncode == 0, result.stdout + result.stderr
    assert expected.stat().st_size == 153088
    assert sha256(expected) == EXE_SHA256


def test_missing_archive_preserves_destination(repository):
    destination = existing_destination(repository)
    before = destination.read_bytes()
    (repository / "third_party" / "hlsavetool" / ARCHIVE_NAME).unlink()
    result = run_installer(repository, destination)
    assert_rejected(result, "archive is missing")
    assert destination.read_bytes() == before


def test_tampered_zip_fails_before_extraction_or_installation(repository):
    destination = existing_destination(repository)
    before = destination.read_bytes()
    archive = repository / "third_party" / "hlsavetool" / ARCHIVE_NAME
    archive.write_bytes(archive.read_bytes() + b"tampered")
    result = run_installer(
        repository, destination,
        'function Expand-Archive { throw "Extraction must not start for a corrupt ZIP" }',
    )
    assert_rejected(result, "archive SHA256 mismatch")
    assert destination.read_bytes() == before


def test_tampered_executable_is_rejected_even_with_matching_zip_pin(repository):
    destination = existing_destination(repository)
    before = destination.read_bytes()
    change_test_archive(
        repository,
        lambda members: members.update({"hlsaves.exe": members["hlsaves.exe"] + b"tampered"}),
    )
    result = run_installer(repository, destination)
    assert_rejected(result, "Extracted hlsaves.exe SHA256 mismatch")
    assert destination.read_bytes() == before


@pytest.mark.parametrize("duplicate", [False, True])
def test_archive_requires_exactly_one_executable(repository, duplicate):
    def change(members):
        if duplicate:
            members["nested/hlsaves.exe"] = members["hlsaves.exe"]
        else:
            del members["hlsaves.exe"]

    change_test_archive(repository, change)
    result = run_installer(repository)
    assert_rejected(result, "must contain exactly one hlsaves.exe")
    assert not (repository / "assets" / "hlsaves.exe").exists()


def test_final_copied_executable_is_verified(repository):
    result = run_installer(repository, before_install=r"""
function Copy-Item {
    param([string]$LiteralPath, [string]$Destination, [switch]$Force)
    Microsoft.PowerShell.Management\Copy-Item @PSBoundParameters
    [System.IO.File]::AppendAllText($Destination, "simulated copy corruption")
}
""")
    assert_rejected(result, "Installed hlsaves.exe SHA256 mismatch")
