[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CliArguments
)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VirtualPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $VirtualPython)) {
    Write-Error "The local environment is not installed. Run .\setup.ps1 first."
    exit 1
}

Push-Location $ProjectRoot
try {
    & $VirtualPython -m src.cli @CliArguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
