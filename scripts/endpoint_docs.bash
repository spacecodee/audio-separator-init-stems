#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/.env_loader.bash"

BASE="${BASE:-${DEFAULT_BASE:-http://localhost:8000}}"
OUT="${OUT:-${DOCS_OUT:-./docs.html}}"

curl -sS "$BASE/docs" -o "$OUT"
echo "Swagger UI guardado en: $OUT"
