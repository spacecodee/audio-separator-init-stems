#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8000}"
JOB_ID="${1:-${JOB_ID:-}}"

if [[ -z "$JOB_ID" ]]; then
  echo "Uso: $0 <job_id>" >&2
  exit 1
fi

curl -sS -X DELETE "$BASE/jobs/$JOB_ID" | python3 -m json.tool
