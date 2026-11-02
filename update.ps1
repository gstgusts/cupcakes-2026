# Switches to main, pulls the latest changes and starts all services (start.ps1)
Push-Location $PSScriptRoot
try {
    git switch main
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    # Only fast-forward: stops instead of creating a merge commit if local main has diverged
    git pull --ff-only
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    & "$PSScriptRoot\start.ps1"
}
finally {
    Pop-Location
}
