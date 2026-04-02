#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8000}"
OUT="${OUT:-./models-explorer.css}"

curl -sS "$BASE/models-explorer.css" -o "$OUT"
echo "CSS guardado en: $OUT"
