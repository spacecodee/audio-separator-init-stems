BASE="http://localhost:8000"
AUDIO="/teamspace/studios/this_studio/audio/12 - Love Me.flac"

JOB=$(curl -s -X POST "$BASE/separate/pipeline" \
    -F "file=@$AUDIO" \
    -F "step1_model=bs_roformer" \
    -F "step2_model=mel_karaoke_gabox" \
    -F "step3_model=dereverb_echo" \
-F "output_format=wav" | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")

echo "Job: $JOB"

while true; do
    RESP=$(curl -s "$BASE/jobs/$JOB")
    STATUS=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
    echo "Estado: $STATUS"
    [ "$STATUS" = "done" ] && echo "$RESP" && break
    [ "$STATUS" = "error" ] && echo "$RESP" && break
    sleep 5
done