#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/.env_loader.bash"

BASE="${BASE:-${DEFAULT_BASE:-http://localhost:8000}}"
OUT="${OUT:-${MODELS_EXPLORER_JS_OUT:-./models-explorer.js}}"

curl -sS "$BASE/models-explorer.js" -o "$OUT"
echo "JS guardado en: $OUT"
