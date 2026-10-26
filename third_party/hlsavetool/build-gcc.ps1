param(
    [Parameter(Mandatory=$true)][string]$Gcc,
    [Parameter(Mandatory=$true)][string]$Source,
    [Parameter(Mandatory=$true)][string]$Output
)
$ErrorActionPreference = 'Stop'
# Source must be upstream 1bab30e plus HL-02A, HL-02C and HL-02D in that order.
# The distribution ZIP also includes this exact patched MIT source.
$Source = (Resolve-Path -LiteralPath $Source).ProviderPath
$Output = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Output)
if (Test-Path -LiteralPath $Output) { throw 'Refusing to overwrite an existing executable' }
$env:PATH = (Split-Path -Parent $Gcc) + ';' + $env:PATH
& $Gcc -O2 -static '-Wl,--no-insert-timestamp' -include "$Source/headers/common.h" `
    "-I$Source/headers" "$Source/src/hlsaves.c" "$Source/src/oodle.c" -o $Output
if ($LASTEXITCODE -ne 0) { throw 'Native build failed' }
Get-FileHash -Algorithm SHA256 -LiteralPath $Output
