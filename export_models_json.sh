#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/scripts/.env_loader.bash"

SERVICE_NAME="${1:-${SERVICE_NAME:-${EXPORT_MODELS_SERVICE_NAME:-stem-separator}}}"
OUTPUT_FILE="${2:-${OUTPUT_FILE:-${EXPORT_MODELS_OUTPUT_FILE:-./models.json}}}"

if docker compose ps --services --filter status=running | grep -qx "$SERVICE_NAME"; then
  docker compose exec -T "$SERVICE_NAME" audio-separator -l --list_format=json > "$OUTPUT_FILE"
else
  docker compose run --rm "$SERVICE_NAME" audio-separator -l --list_format=json > "$OUTPUT_FILE"
fi

echo "Model list exported to $OUTPUT_FILE"
