#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/.env_loader.bash"

BASE="${BASE:-${DEFAULT_BASE:-http://localhost:8000}}"
OUT="${OUT:-${MODELS_EXPLORER_CSS_OUT:-./models-explorer.css}}"

curl -sS "$BASE/models-explorer.css" -o "$OUT"
echo "CSS guardado en: $OUT"
