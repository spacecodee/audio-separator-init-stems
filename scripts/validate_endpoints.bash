#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
FAILED=0

check_contains() {
  local script_name="$1"
  local expected="$2"
  local file="$SCRIPT_DIR/$script_name"

  if grep -Fq "$expected" "$file"; then
    echo "OK   $script_name -> $expected"
  else
    echo "FAIL $script_name -> expected: $expected" >&2
    FAILED=1
  fi
}

check_contains_file() {
  local file="$1"
  local label="$2"
  local expected="$3"

  if grep -Fq "$expected" "$file"; then
    echo "OK   $label -> $expected"
  else
    echo "FAIL $label -> expected: $expected" >&2
    FAILED=1
  fi
}

check_contains "endpoint_root.bash" '"$BASE/"'
check_contains "endpoint_models.bash" '"$BASE/models"'
check_contains "endpoint_docs.bash" '"$BASE/docs"'
check_contains "endpoint_openapi_json.bash" '"$BASE/openapi.json"'
check_contains "endpoint_models_explorer.bash" '"$BASE/models-explorer"'
check_contains "endpoint_models_explorer_html.bash" '"$BASE/models-explorer.html"'
check_contains "endpoint_models_explorer_css.bash" '"$BASE/models-explorer.css"'
check_contains "endpoint_models_explorer_js.bash" '"$BASE/models-explorer.js"'
check_contains "endpoint_models_json.bash" '"$BASE/models.json"'
check_contains "endpoint_jobs_list.bash" '"$BASE/jobs"'
check_contains "endpoint_job_status.bash" '"$BASE/jobs/$JOB_ID"'
check_contains "endpoint_job_delete.bash" '"$BASE/jobs/$JOB_ID"'
check_contains "endpoint_download.bash" '"$BASE/download/$JOB_ID/$FILENAME"'
check_contains "endpoint_separate.bash" '"$BASE/separate"'
check_contains "endpoint_separate_pipeline.bash" '"$BASE/separate/pipeline"'
check_contains "endpoint_separate_guitar_pipeline.bash" '"$BASE/separate/guitar/pipeline"'
check_contains "endpoint_separate_vocals_reconstruct.bash" '"$BASE/separate/vocals/reconstruct"'
check_contains "endpoint_separate_vocals_male_female.bash" '"$BASE/separate/vocals/male-female"'
check_contains "endpoint_effects_dereverb.bash" '"$BASE/effects/dereverb"'
check_contains "endpoint_effects_deecho.bash" '"$BASE/effects/deecho"'
check_contains "endpoint_effects_dereverb_deecho.bash" '"$BASE/effects/dereverb-deecho"'

for async_script in \
  endpoint_separate.bash \
  endpoint_separate_pipeline.bash \
  endpoint_separate_guitar_pipeline.bash \
  endpoint_separate_vocals_reconstruct.bash \
  endpoint_separate_vocals_male_female.bash \
  endpoint_effects_dereverb.bash \
  endpoint_effects_deecho.bash \
  endpoint_effects_dereverb_deecho.bash

do
  check_contains "$async_script" '"$BASE/jobs/$JOB_ID"'
done

check_contains_file "$PROJECT_DIR/app.bash" "app.bash" '"$BASE/separate/pipeline"'
check_contains_file "$PROJECT_DIR/app.bash" "app.bash" '"$BASE/jobs/$JOB"'

if [[ "$FAILED" -eq 0 ]]; then
  echo "All endpoint scripts point to expected API routes."
else
  exit 1
fi
