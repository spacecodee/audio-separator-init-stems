#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/.env_loader.bash"

BASE="${BASE:-${DEFAULT_BASE:-http://localhost:8000}}"
JOB_ID="${1:-${JOB_ID:-}}"
FILENAME="${2:-${FILENAME:-}}"
OUT_DIR="${OUT_DIR:-${DOWNLOAD_OUT_DIR:-.}}"

if [[ -z "$JOB_ID" || -z "$FILENAME" ]]; then
  echo "Uso: $0 <job_id> <filename>" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
TARGET="$OUT_DIR/$FILENAME"

curl -fsSL "$BASE/download/$JOB_ID/$FILENAME" -o "$TARGET"
echo "Archivo descargado en: $TARGET"
