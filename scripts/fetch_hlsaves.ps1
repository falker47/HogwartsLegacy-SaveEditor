param(
    [string]$Destination
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $Destination) {
    $Destination = Join-Path $RepoRoot "assets\hlsaves.exe"
}

$Version = "2.0.1"
$ArchiveUrl = "https://github.com/gx570s/hlsavetool/releases/download/v$Version/HLSaveToolv$Version.zip"
$ExpectedArchiveSha256 = "a5733229c767f451d0b2612df88af2823e84e769b482d9b0eebe7f6fc09472ed"

$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("hlsavetool-" + [guid]::NewGuid().ToString("N"))
$ArchivePath = Join-Path $TempRoot "hlsavetool.zip"
$ExtractPath = Join-Path $TempRoot "extract"

try {
    New-Item -ItemType Directory -Force -Path $TempRoot | Out-Null
    New-Item -ItemType Directory -Force -Path $ExtractPath | Out-Null
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null

    Write-Host "Downloading hlsavetool v$Version from upstream GitHub release..."
    Invoke-WebRequest -Uri $ArchiveUrl -OutFile $ArchivePath -UseBasicParsing

    $ActualArchiveSha256 = (Get-FileHash -Algorithm SHA256 -Path $ArchivePath).Hash.ToLowerInvariant()
    if ($ActualArchiveSha256 -ne $ExpectedArchiveSha256) {
        throw "hlsavetool archive SHA256 mismatch. Expected $ExpectedArchiveSha256, got $ActualArchiveSha256."
    }

    Expand-Archive -Path $ArchivePath -DestinationPath $ExtractPath -Force
    $Exe = Get-ChildItem -Path $ExtractPath -Recurse -File -Filter "hlsaves.exe" | Select-Object -First 1
    if (-not $Exe) {
        throw "The verified upstream archive did not contain hlsaves.exe."
    }

    Copy-Item -Force -Path $Exe.FullName -Destination $Destination
    Write-Host "Installed hlsaves.exe v$Version to $Destination"
}
finally {
    if (Test-Path $TempRoot) {
        Remove-Item -Recurse -Force $TempRoot
    }
}
