#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8000}"
AUDIO="${AUDIO:-/teamspace/studios/this_studio/audio/Audio03.wav}"
COMBINED_MODEL="${COMBINED_MODEL:-dereverb_echo}"
FALLBACK_SEQUENTIAL="${FALLBACK_SEQUENTIAL:-true}"
FALLBACK_DEREVERB_MODEL="${FALLBACK_DEREVERB_MODEL:-dereverb_mel}"
FALLBACK_DEECHO_MODEL="${FALLBACK_DEECHO_MODEL:-deecho_normal}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-wav}"
POLL_SECONDS="${POLL_SECONDS:-5}"

[[ -f "$AUDIO" ]] || { echo "No existe el audio: $AUDIO" >&2; exit 1; }

JOB_RESPONSE="$(curl -sS -X POST "$BASE/effects/dereverb-deecho" \
  -F "file=@$AUDIO" \
  -F "combined_model=$COMBINED_MODEL" \
  -F "fallback_sequential=$FALLBACK_SEQUENTIAL" \
  -F "fallback_dereverb_model=$FALLBACK_DEREVERB_MODEL" \
  -F "fallback_deecho_model=$FALLBACK_DEECHO_MODEL" \
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
