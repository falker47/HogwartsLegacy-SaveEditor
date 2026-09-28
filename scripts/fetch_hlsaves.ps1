param(
    [string]$Destination
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $Destination) {
    $Destination = Join-Path $RepoRoot "assets/hlsaves.exe"
}
$Destination = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Destination)

$Version = "2.0.1-hl02a.1"
$ArchivePath = Join-Path $RepoRoot "third_party/hlsavetool/HLSaveToolv$Version.zip"
$ExpectedArchiveSha256 = "eeedcc913d1ea916e9edc6b599002bac7823a9989050b79851b5f9f02c0b7a75"
$ExpectedExeSha256 = "bdf28ae18dc5ecf049af37ca863085851f2cd0f5b22895f9637c5820c8d0f70e"

if (-not (Test-Path -LiteralPath $ArchivePath -PathType Leaf)) {
    throw "Vendored hlsavetool archive is missing: $ArchivePath. Restore it from this repository."
}
$ActualArchiveSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $ArchivePath).Hash.ToLowerInvariant()
if ($ActualArchiveSha256 -ne $ExpectedArchiveSha256) {
    throw "Vendored hlsavetool archive SHA256 mismatch. Expected $ExpectedArchiveSha256, got $ActualArchiveSha256."
}

$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("hlsavetool-" + [guid]::NewGuid().ToString("N"))
$ExtractPath = Join-Path $TempRoot "extract"

try {
    New-Item -ItemType Directory -Path $ExtractPath -Force | Out-Null
    Write-Host "Installing verified vendored hlsavetool v$Version..."
    Expand-Archive -LiteralPath $ArchivePath -DestinationPath $ExtractPath

    $Executables = @(Get-ChildItem -LiteralPath $ExtractPath -Recurse -File -Filter "hlsaves.exe")
    if ($Executables.Count -ne 1) {
        throw "The vendored hlsavetool archive must contain exactly one hlsaves.exe."
    }
    $Exe = $Executables[0]
    $ActualExeSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Exe.FullName).Hash.ToLowerInvariant()
    if ($ActualExeSha256 -ne $ExpectedExeSha256) {
        throw "Extracted hlsaves.exe SHA256 mismatch. Expected $ExpectedExeSha256, got $ActualExeSha256."
    }

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
    Copy-Item -Force -LiteralPath $Exe.FullName -Destination $Destination
    $InstalledExeSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Destination).Hash.ToLowerInvariant()
    if ($InstalledExeSha256 -ne $ExpectedExeSha256) {
        throw "Installed hlsaves.exe SHA256 mismatch. Expected $ExpectedExeSha256, got $InstalledExeSha256."
    }
    Write-Host "Installed verified hlsaves.exe v$Version to $Destination"
}
finally {
    if (Test-Path -LiteralPath $TempRoot) {
        $ResolvedTempRoot = (Resolve-Path -LiteralPath $TempRoot).ProviderPath
        if ($ResolvedTempRoot -ne [System.IO.Path]::GetFullPath($TempRoot)) {
            throw "Unexpected temporary directory path; refusing cleanup: $ResolvedTempRoot"
        }
        Remove-Item -Recurse -Force -LiteralPath $ResolvedTempRoot
    }
}
