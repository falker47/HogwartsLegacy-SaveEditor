param(
    [string]$Destination
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $Destination) {
    $Destination = Join-Path $RepoRoot "assets/hlsaves.exe"
}
$Destination = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Destination)

$Version = "2.0.1-hl02acd.1"
$ArchivePath = Join-Path $RepoRoot "third_party/hlsavetool/HLSaveToolv$Version.zip"
$ExpectedArchiveSha256 = "d3aeb8f6c8a8faab3c67041f0265a06446cdc71e9abc876b3a632293ea3f77fc"
$ExpectedExeSha256 = "4080b409c125c29a3b977ed42160e36fb422fe0eaaa7f0c5d9419737a81cd3bb"

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
