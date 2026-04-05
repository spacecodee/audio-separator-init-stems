#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$ROOT_DIR/scripts/.env_loader.bash"

PORT="${1:-${MODELS_EXPLORER_PORT:-8088}}"

cd "$ROOT_DIR"

echo "Serving Models Explorer at: http://127.0.0.1:${PORT}/models-explorer.html"
python3 -m http.server "$PORT"
