#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${1:-stem-separator}"
OUTPUT_FILE="${2:-./models.json}"

if docker compose ps --services --filter status=running | grep -qx "$SERVICE_NAME"; then
  docker compose exec -T "$SERVICE_NAME" audio-separator -l --list_format=json > "$OUTPUT_FILE"
else
  docker compose run --rm "$SERVICE_NAME" audio-separator -l --list_format=json > "$OUTPUT_FILE"
fi

echo "Model list exported to $OUTPUT_FILE"
