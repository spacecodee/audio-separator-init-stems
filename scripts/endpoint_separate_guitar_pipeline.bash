#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8000}"
AUDIO="${AUDIO:-/teamspace/studios/this_studio/audio/Audio04.wav}"
SPLIT_MODEL="${SPLIT_MODEL:-htdemucs_6s}"
DEREVERB_MODEL="${DEREVERB_MODEL:-dereverb_mel}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-wav}"
POLL_SECONDS="${POLL_SECONDS:-5}"

[[ -f "$AUDIO" ]] || { echo "No existe el audio: $AUDIO" >&2; exit 1; }

JOB_RESPONSE="$(curl -sS -X POST "$BASE/separate/guitar/pipeline" \
  -F "file=@$AUDIO" \
  -F "split_model=$SPLIT_MODEL" \
  -F "dereverb_model=$DEREVERB_MODEL" \
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
