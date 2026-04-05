#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/.env_loader.bash"

BASE="${BASE:-${DEFAULT_BASE:-http://localhost:8000}}"
JOB_ID="${1:-${JOB_ID:-}}"

if [[ -z "$JOB_ID" ]]; then
  echo "Uso: $0 <job_id>" >&2
  exit 1
fi

curl -sS -X DELETE "$BASE/jobs/$JOB_ID" | python3 -m json.tool
