#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8000}"

curl -sS "$BASE/models" | python3 -m json.tool
