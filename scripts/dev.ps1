$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root "venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Error "Virtual environment not found at $python"
    exit 1
}

& $python (Join-Path $root "run.py") @args
exit $LASTEXITCODE
