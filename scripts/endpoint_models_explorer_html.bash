#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8000}"
OUT="${OUT:-./models-explorer.alias.html}"

curl -sS "$BASE/models-explorer.html" -o "$OUT"
echo "Alias HTML guardado en: $OUT"
