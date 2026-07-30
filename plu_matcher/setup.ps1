[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VirtualEnvironment = Join-Path $ProjectRoot ".venv"
$VirtualPython = Join-Path $VirtualEnvironment "Scripts\python.exe"

Push-Location $ProjectRoot
try {
    if (-not (Test-Path -LiteralPath $VirtualPython)) {
        $PythonLauncher = Get-Command py -ErrorAction SilentlyContinue
        if ($PythonLauncher) {
            & py -3 -m venv $VirtualEnvironment
        }
        else {
            $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
            if (-not $PythonCommand) {
                throw "Python 3.11 or newer was not found on PATH."
            }
            & python -m venv $VirtualEnvironment
        }
    }

    & $VirtualPython -m pip install --upgrade pip
    & $VirtualPython -m pip install -e ".[dev]"

    $InputsDirectory = Join-Path $ProjectRoot "inputs"
    if (-not (Test-Path -LiteralPath $InputsDirectory)) {
        New-Item -ItemType Directory -Path $InputsDirectory | Out-Null
    }

    $EnvironmentFile = Join-Path $ProjectRoot ".env"
    if (-not (Test-Path -LiteralPath $EnvironmentFile)) {
        Copy-Item -LiteralPath (Join-Path $ProjectRoot ".env.example") -Destination $EnvironmentFile
        Write-Host ""
        Write-Host "Created .env from .env.example."
        Write-Host "Add the approved QU credentials before making a live request."
    }

    $DemoWorkbook = Join-Path $InputsDirectory "Aloha_Qu_Menu_Demo.xlsx"
    $DemoMenu = Join-Path $ProjectRoot "cache\99999-1-1\menu.json"
    if (
        -not (Test-Path -LiteralPath $DemoWorkbook) -or
        -not (Test-Path -LiteralPath $DemoMenu)
    ) {
        & $VirtualPython -m scripts.create_demo_data --force
        if ($LASTEXITCODE -ne 0) {
            throw "Could not create the sanitized offline demo data."
        }
    }

    & $VirtualPython -m pytest -q
    if ($LASTEXITCODE -ne 0) {
        throw "Setup completed, but the test suite failed."
    }

    Write-Host ""
    Write-Host "Setup complete."
    Write-Host "Offline demo: .\run.ps1 run --location demo --offline"
    Write-Host "Next: .\run.ps1 status --location atlanta"
}
finally {
    Pop-Location
}
