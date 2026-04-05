#!/usr/bin/env bash

SCRIPT_DIR_ENV_LOADER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR_ENV_LOADER="$(cd "$SCRIPT_DIR_ENV_LOADER/.." && pwd)"
ENV_FILE_PATH="${PROJECT_ENV_FILE:-$PROJECT_DIR_ENV_LOADER/.env}"

if [[ -f "$ENV_FILE_PATH" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE_PATH"
  set +a
fi
