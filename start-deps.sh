#!/usr/bin/env sh
# Starts only what the Flask app needs (PostgreSQL, Keycloak) and builds the Tailwind CSS,
# so the app itself can run locally, e.g. in the VS Code debugger
set -e
cd "$(dirname "$0")"

# Free port 5000 in case the full stack (start.sh) is running
docker compose stop web
docker compose up -d db keycloak
docker compose run --rm css

printf "Waiting for Keycloak"
tries=0
until curl -sf -o /dev/null http://localhost:8080/realms/cupcakes; do
    tries=$((tries + 1))
    if [ "$tries" -ge 60 ]; then echo " not ready after 2 minutes, check: docker compose logs keycloak"; exit 1; fi
    printf "."
    sleep 2
done
echo " ready"

echo ""
echo "Postgres: localhost:5432"
echo "Keycloak: http://localhost:8080  (admin / admin)"
echo "Now start Flask: F5 in VS Code, or: flask --app run run --debug"
