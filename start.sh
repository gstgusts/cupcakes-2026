#!/usr/bin/env sh
# Builds the web image and starts all services (db, keycloak, web) in the background
set -e
cd "$(dirname "$0")"

docker compose up -d --build

echo ""
echo "Web:      http://localhost:5000"
echo "Keycloak: http://localhost:8080  (admin / admin)"
echo "Stop:     docker compose down"
