# Adds demo cupcakes, prediction models and predictions to the running app (only the missing ones)
Push-Location $PSScriptRoot
try {
    docker compose exec web flask --app run seed-demo
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}
