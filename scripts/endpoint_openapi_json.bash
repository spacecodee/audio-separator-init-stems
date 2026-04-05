#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/.env_loader.bash"

BASE="${BASE:-${DEFAULT_BASE:-http://localhost:8000}}"
OUT="${OUT:-${OPENAPI_JSON_OUT:-./openapi.json}}"

curl -sS "$BASE/openapi.json" -o "$OUT"
echo "OpenAPI guardado en: $OUT"
