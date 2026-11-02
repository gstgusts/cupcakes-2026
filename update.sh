#!/usr/bin/env sh
# Switches to main, pulls the latest changes and starts all services (start.sh)
set -e
cd "$(dirname "$0")"

git switch main
# Only fast-forward: stops instead of creating a merge commit if local main has diverged
git pull --ff-only

./start.sh
