# Builds the web image and starts all services (db, keycloak, web) in the background
Push-Location $PSScriptRoot
try {
    docker compose up -d --build
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host ""
    Write-Host "Web:      http://localhost:5000"
    Write-Host "Keycloak: http://localhost:8080  (admin / admin)"
    Write-Host "Stop:     docker compose down"
}
finally {
    Pop-Location
}
