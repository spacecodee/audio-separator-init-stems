#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8000}"
OUT="${OUT:-./models-explorer.html}"

curl -sS "$BASE/models-explorer" -o "$OUT"
echo "Models Explorer guardado en: $OUT"
