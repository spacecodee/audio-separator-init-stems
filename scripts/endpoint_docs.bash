#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8000}"
OUT="${OUT:-./docs.html}"

curl -sS "$BASE/docs" -o "$OUT"
echo "Swagger UI guardado en: $OUT"
