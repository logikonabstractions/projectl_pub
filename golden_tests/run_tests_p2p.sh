#!/usr/bin/env bash
# P2P (pass-to-pass) regression checks — must pass before and after any change.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

echo "=== P2P: tests/test_game_integration.py ==="
python -m pytest tests/test_game_integration.py -v
