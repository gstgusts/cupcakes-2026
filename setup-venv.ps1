# Creates the .venv virtual environment (if missing) and installs requirements-dev.txt (app + test tools) into it
Push-Location $PSScriptRoot
try {
    if (-not (Test-Path .venv)) {
        # Prefer the Windows Python launcher, fall back to python on PATH
        if (Get-Command py -ErrorAction SilentlyContinue) { py -3 -m venv .venv }
        else { python -m venv .venv }
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }

    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host ""
    Write-Host "Done. Activate the environment with:"
    Write-Host "  .\.venv\Scripts\Activate.ps1"
}
finally {
    Pop-Location
}
