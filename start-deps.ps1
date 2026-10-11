# Starts only what the Flask app needs (PostgreSQL, Keycloak) and builds the Tailwind CSS,
# so the app itself can run locally, e.g. in the VS Code debugger
Push-Location $PSScriptRoot
try {
    # Free port 5000 in case the full stack (start.ps1) is running
    docker compose stop web
    docker compose up -d db keycloak
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    docker compose run --rm css
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host -NoNewline "Waiting for Keycloak"
    $ready = $false
    foreach ($i in 1..60) {
        try {
            Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://localhost:8080/realms/cupcakes | Out-Null
            $ready = $true
            break
        }
        catch {
            Write-Host -NoNewline "."
            Start-Sleep -Seconds 2
        }
    }
    if (-not $ready) {
        Write-Host " not ready after 2 minutes, check: docker compose logs keycloak"
        exit 1
    }
    Write-Host " ready"

    Write-Host ""
    Write-Host "Postgres: localhost:5432"
    Write-Host "Keycloak: http://localhost:8080  (admin / admin)"
    Write-Host "Now start Flask: F5 in VS Code, or: flask --app run run --debug"
}
finally {
    Pop-Location
}
