#!/usr/bin/env bash
set -euo pipefail

base_url="${BASE_URL:-http://localhost}"
health_url="${base_url%/}/v1/health"

python3 - "$health_url" <<'PY'
import json
import sys
import urllib.request

url = sys.argv[1]
with urllib.request.urlopen(url, timeout=10) as response:
    payload = json.load(response)

if payload.get("success") is not True:
    raise SystemExit("health response did not report success")

data = payload.get("data") or {}
if data.get("status") != "UP":
    raise SystemExit(f"unexpected health status: {data.get('status')!r}")

if payload.get("message") != "Success":
    raise SystemExit(f"unexpected health message: {payload.get('message')!r}")
PY
