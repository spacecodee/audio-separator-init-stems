#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8000}"

curl -sS "$BASE/" | python3 -m json.tool
