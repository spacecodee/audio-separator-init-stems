#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8000}"
OUT="${OUT:-./models.json}"

curl -sS "$BASE/models.json" -o "$OUT"
echo "models.json guardado en: $OUT"
