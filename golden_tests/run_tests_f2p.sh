#!/usr/bin/env bash
# F2P (fail-to-pass) checks — expected to fail before the fix, pass after.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

echo "=== F2P: golden_test/test_pieces.py ==="
python -m pytest golden_test/test_pieces.py -v

echo "=== F2P: golden_test/test_cards.py ==="
python -m pytest golden_test/test_cards.py -v
