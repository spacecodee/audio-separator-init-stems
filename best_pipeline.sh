#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/scripts/.env_loader.bash"

PROJECT_DIR="$SCRIPT_DIR"
INPUT_DIR_HOST="$PROJECT_DIR/input"
OUTPUT_DIR_HOST="$PROJECT_DIR/output"

SERVICE_NAME="${SERVICE_NAME:-stem-separator}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-wav}"
DEREVERB_MODEL="${DEREVERB_MODEL:-${BEST_PIPELINE_DEREVERB_MODEL:-dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt}}"
KARAOKE_SPLIT_MODEL="${KARAOKE_SPLIT_MODEL:-${BEST_PIPELINE_KARAOKE_SPLIT_MODEL:-mel_band_roformer_karaoke_aufr33_viperx_sdr_10.1956.ckpt}}"

OUTPUT_FORMAT="$(printf '%s' "$OUTPUT_FORMAT" | tr '[:upper:]' '[:lower:]')"

log() {
  printf '[best-pipeline] %s\n' "$*"
}

die() {
  printf '[best-pipeline] ERROR: %s\n' "$*" >&2
  exit 1
}

usage() {
  cat <<'EOF'
Usage:
  ./best_pipeline.sh <mode> <input_audio> [output_tag]

Modes:
  acapella
  karaoke-backing
  karaoke+backing
  multistem
  multistem+drumsep+dereverb

Examples:
  ./best_pipeline.sh acapella ./input/song.wav
  ./best_pipeline.sh karaoke+backing ./input/song.wav my_song_run
  ./best_pipeline.sh multistem+drumsep+dereverb ./input/song.wav

Environment variables:
  SERVICE_NAME       Docker Compose service name (default: stem-separator)
  OUTPUT_FORMAT      wav|flac|mp3 (default: wav)
  DEREVERB_MODEL     Model for dereverb step
  KARAOKE_SPLIT_MODEL Model used to split lead/backing proxy from vocals

Notes:
  - Requires the compose service to be running.
  - Input files are copied into ./input if they are outside that folder.
  - Outputs are written under ./output/<output_tag>/
EOF
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

require_running_service() {
  if ! docker compose ps --services --filter status=running | grep -qx "$SERVICE_NAME"; then
    die "Service '$SERVICE_NAME' is not running. Start it with: docker compose up -d"
  fi
}

sanitize_name() {
  local value="$1"
  value="${value// /_}"
  value="${value//\//_}"
  value="${value//+/plus}"
  printf '%s' "$value" | tr -cd 'A-Za-z0-9._-'
}

latest_match() {
  local search_dir="$1"
  local pattern="$2"
  find "$search_dir" -type f -iname "$pattern" -printf '%T@|%p\n' 2>/dev/null \
    | sort -t '|' -nr \
    | head -n 1 \
    | cut -d '|' -f2-
}

host_output_to_container() {
  local host_path="$1"
  if [[ "$host_path" != "$OUTPUT_DIR_HOST"* ]]; then
    die "Path is outside output mount: $host_path"
  fi
  printf '/app/output%s\n' "${host_path#$OUTPUT_DIR_HOST}"
}

stage_input_to_container() {
  local user_input="$1"

  if [[ "$user_input" == /app/input/* ]]; then
    printf '%s\n' "$user_input"
    return
  fi

  [[ -f "$user_input" ]] || die "Input file not found: $user_input"

  mkdir -p "$INPUT_DIR_HOST"

  local abs_input
  abs_input="$(cd "$(dirname "$user_input")" && pwd)/$(basename "$user_input")"
  local dest_host="$INPUT_DIR_HOST/$(basename "$abs_input")"

  if [[ "$abs_input" != "$dest_host" ]]; then
    cp -f "$abs_input" "$dest_host"
    log "Copied input to $dest_host"
  fi

  printf '/app/input/%s\n' "$(basename "$dest_host")"
}

run_separator() {
  docker compose exec -T "$SERVICE_NAME" audio-separator "$@"
}

run_acapella() {
  local input_container="$1"
  local mode_output_host="$2"

  mkdir -p "$mode_output_host"
  local mode_output_container
  mode_output_container="$(host_output_to_container "$mode_output_host")"

  log "Mode: acapella"
  run_separator "$input_container" \
    --output_dir "$mode_output_container" \
    --ensemble_preset vocal_full \
    --single_stem Vocals \
    --output_format "$OUTPUT_FORMAT"
}

run_karaoke_backing() {
  local input_container="$1"
  local mode_output_host="$2"

  local step1_host="$mode_output_host/01_vocal_full"
  local step2_host="$mode_output_host/02_lead_backing_proxy"
  local step3_host="$mode_output_host/03_instrumental_karaoke"

  mkdir -p "$step1_host" "$step2_host" "$step3_host"

  local step1_container step2_container step3_container
  step1_container="$(host_output_to_container "$step1_host")"
  step2_container="$(host_output_to_container "$step2_host")"
  step3_container="$(host_output_to_container "$step3_host")"

  log "Mode: karaoke-backing"
  log "Step 1: extract full vocals"
  run_separator "$input_container" \
    --output_dir "$step1_container" \
    --ensemble_preset vocal_full \
    --single_stem Vocals \
    --output_format "$OUTPUT_FORMAT"

  local vocals_host
  vocals_host="$(latest_match "$step1_host" "*vocals*.${OUTPUT_FORMAT}")"
  [[ -n "$vocals_host" ]] || vocals_host="$(latest_match "$step1_host" "*vocals*")"
  [[ -n "$vocals_host" ]] || die "Could not find vocals output from step 1"

  local vocals_container
  vocals_container="$(host_output_to_container "$vocals_host")"

  log "Step 2: split lead/backing proxy from vocals"
  run_separator "$vocals_container" \
    --output_dir "$step2_container" \
    -m "$KARAOKE_SPLIT_MODEL" \
    --output_format "$OUTPUT_FORMAT"

  local lead_host backing_host
  lead_host="$(latest_match "$step2_host" "*vocals*.${OUTPUT_FORMAT}")"
  backing_host="$(latest_match "$step2_host" "*instrumental*.${OUTPUT_FORMAT}")"

  if [[ -n "$lead_host" ]]; then
    mv -f "$lead_host" "$step2_host/lead_vocals.${OUTPUT_FORMAT}"
  fi
  if [[ -n "$backing_host" ]]; then
    mv -f "$backing_host" "$step2_host/backing_vocals_proxy.${OUTPUT_FORMAT}"
  fi

  log "Step 3: extract karaoke instrumental"
  run_separator "$input_container" \
    --output_dir "$step3_container" \
    --ensemble_preset karaoke \
    --single_stem Instrumental \
    --output_format "$OUTPUT_FORMAT"
}

run_multistem() {
  local input_container="$1"
  local mode_output_host="$2"

  local step1_host="$mode_output_host/01_6stem"
  local step2_host="$mode_output_host/02_drumsep"
  local step3_host="$mode_output_host/03_dereverb_vocals"

  mkdir -p "$step1_host" "$step2_host" "$step3_host"

  local step1_container step2_container step3_container
  step1_container="$(host_output_to_container "$step1_host")"
  step2_container="$(host_output_to_container "$step2_host")"
  step3_container="$(host_output_to_container "$step3_host")"

  log "Mode: multistem"
  log "Step 1: 6 stem separation"
  run_separator "$input_container" \
    --output_dir "$step1_container" \
    -m htdemucs_6s.yaml \
    --output_format "$OUTPUT_FORMAT"

  local drums_host vocals_host
  drums_host="$(latest_match "$step1_host" "*drums*.${OUTPUT_FORMAT}")"
  [[ -n "$drums_host" ]] || drums_host="$(latest_match "$step1_host" "*drums*")"

  vocals_host="$(latest_match "$step1_host" "*vocals*.${OUTPUT_FORMAT}")"
  [[ -n "$vocals_host" ]] || vocals_host="$(latest_match "$step1_host" "*vocals*")"

  if [[ -n "$drums_host" ]]; then
    log "Step 2: drum sub-stems"
    run_separator "$(host_output_to_container "$drums_host")" \
      --output_dir "$step2_container" \
      -m MDX23C-DrumSep-aufr33-jarredou.ckpt \
      --output_format "$OUTPUT_FORMAT"
  else
    log "Step 2 skipped: drums stem not found"
  fi

  if [[ -n "$vocals_host" ]]; then
    log "Step 3: dereverb vocals"
    run_separator "$(host_output_to_container "$vocals_host")" \
      --output_dir "$step3_container" \
      -m "$DEREVERB_MODEL" \
      --output_format "$OUTPUT_FORMAT"
  else
    log "Step 3 skipped: vocals stem not found"
  fi
}

main() {
  require_command docker
  require_running_service

  local mode_raw="${1:-}"
  local input_arg="${2:-}"
  local output_tag="${3:-}"

  if [[ -z "$mode_raw" || -z "$input_arg" ]]; then
    usage
    exit 1
  fi

  if [[ "$mode_raw" == "-h" || "$mode_raw" == "--help" ]]; then
    usage
    exit 0
  fi

  local mode
  case "$mode_raw" in
    acapella)
      mode="acapella"
      ;;
    karaoke-backing|karaoke+backing|karaoke_backing)
      mode="karaoke-backing"
      ;;
    multistem|multistem+drumsep+dereverb|multistem-drumsep-dereverb)
      mode="multistem"
      ;;
    *)
      die "Unknown mode: $mode_raw"
      ;;
  esac

  local input_container
  input_container="$(stage_input_to_container "$input_arg")"

  local input_base
  input_base="$(basename "$input_container")"
  input_base="${input_base%.*}"

  if [[ -z "$output_tag" ]]; then
    output_tag="$(date +%Y%m%d_%H%M%S)_${mode}_$(sanitize_name "$input_base")"
  fi

  output_tag="$(sanitize_name "$output_tag")"
  [[ -n "$output_tag" ]] || die "Invalid output tag"

  local mode_output_host="$OUTPUT_DIR_HOST/$output_tag"
  mkdir -p "$mode_output_host"

  case "$mode" in
    acapella)
      run_acapella "$input_container" "$mode_output_host"
      ;;
    karaoke-backing)
      run_karaoke_backing "$input_container" "$mode_output_host"
      ;;
    multistem)
      run_multistem "$input_container" "$mode_output_host"
      ;;
  esac

  log "Done"
  log "Output folder: $mode_output_host"
}

main "$@"
