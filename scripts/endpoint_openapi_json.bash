#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8000}"
OUT="${OUT:-./openapi.json}"

curl -sS "$BASE/openapi.json" -o "$OUT"
echo "OpenAPI guardado en: $OUT"
