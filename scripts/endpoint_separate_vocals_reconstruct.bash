#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/.env_loader.bash"

BASE="${BASE:-${DEFAULT_BASE:-http://localhost:8000}}"
AUDIO="${AUDIO:-${VOCALS_RECONSTRUCT_AUDIO:-${DEFAULT_AUDIO:-/teamspace/studios/this_studio/audio/Audio03.wav}}}"
EXTRACT_MODEL="${EXTRACT_MODEL:-${VOCALS_RECONSTRUCT_EXTRACT_MODEL:-mel_roformer}}"
RECONSTRUCT_MODEL="${RECONSTRUCT_MODEL:-${VOCALS_RECONSTRUCT_MODEL:-vocals_resurrection}}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-${DEFAULT_OUTPUT_FORMAT:-wav}}"
POLL_SECONDS="${POLL_SECONDS:-${DEFAULT_POLL_SECONDS:-5}}"

[[ -f "$AUDIO" ]] || { echo "No existe el audio: $AUDIO" >&2; exit 1; }

JOB_RESPONSE="$(curl -sS -X POST "$BASE/separate/vocals/reconstruct" \
  -F "file=@$AUDIO" \
  -F "extract_model=$EXTRACT_MODEL" \
  -F "reconstruct_model=$RECONSTRUCT_MODEL" \
  -F "output_format=$OUTPUT_FORMAT")"

JOB_ID="$(echo "$JOB_RESPONSE" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("job_id",""))')"
[[ -n "$JOB_ID" ]] || { echo "$JOB_RESPONSE"; exit 1; }

echo "Job: $JOB_ID"

while true; do
  RESP="$(curl -sS "$BASE/jobs/$JOB_ID")"
  STATUS="$(echo "$RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("status","unknown"))')"
  echo "Estado: $STATUS"

  if [[ "$STATUS" == "done" || "$STATUS" == "error" ]]; then
    echo "$RESP" | python3 -m json.tool
    break
  fi

  sleep "$POLL_SECONDS"
done
