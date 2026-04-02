#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8000}"
OUT="${OUT:-./models-explorer.js}"

curl -sS "$BASE/models-explorer.js" -o "$OUT"
echo "JS guardado en: $OUT"
