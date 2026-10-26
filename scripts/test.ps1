$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root "venv\Scripts\python.exe"

Push-Location (Join-Path $root "backend")
try {
    & $python -m pytest @args
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
