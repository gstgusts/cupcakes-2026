#!/usr/bin/env sh
# Adds demo cupcakes, prediction models and predictions to the running app (only the missing ones)
set -e
cd "$(dirname "$0")"

docker compose exec web flask --app run seed-demo
