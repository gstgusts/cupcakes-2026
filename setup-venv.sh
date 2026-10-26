#!/usr/bin/env sh
# Creates the .venv virtual environment (if missing) and installs requirements-dev.txt (app + test tools) into it
set -e
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
    # Pick the first Python that actually runs (on Windows "python3" can be a Store placeholder)
    for PY in python3 python py; do
        if "$PY" -c "import sys" >/dev/null 2>&1; then break; fi
        PY=""
    done
    if [ -z "$PY" ]; then echo "Python not found. Install Python 3 first." >&2; exit 1; fi
    "$PY" -m venv .venv
fi

# Windows (Git Bash) uses Scripts/, macOS/Linux use bin/
if [ -d .venv/Scripts ]; then BIN=.venv/Scripts; else BIN=.venv/bin; fi

"$BIN/python" -m pip install --upgrade pip
"$BIN/python" -m pip install -r requirements-dev.txt

echo ""
echo "Done. Activate the environment with:"
echo "  source $BIN/activate"
