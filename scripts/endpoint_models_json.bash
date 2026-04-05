#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/.env_loader.bash"

BASE="${BASE:-${DEFAULT_BASE:-http://localhost:8000}}"
OUT="${OUT:-${MODELS_JSON_OUT:-./models.json}}"

curl -sS "$BASE/models.json" -o "$OUT"
echo "models.json guardado en: $OUT"
