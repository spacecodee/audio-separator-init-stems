#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8000}"
JOB_ID="${1:-${JOB_ID:-}}"
FILENAME="${2:-${FILENAME:-}}"
OUT_DIR="${OUT_DIR:-.}"

if [[ -z "$JOB_ID" || -z "$FILENAME" ]]; then
  echo "Uso: $0 <job_id> <filename>" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
TARGET="$OUT_DIR/$FILENAME"

curl -fsSL "$BASE/download/$JOB_ID/$FILENAME" -o "$TARGET"
echo "Archivo descargado en: $TARGET"
