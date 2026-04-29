#!/usr/bin/env bash
set -euo pipefail

curl --fail --silent --show-error "http://127.0.0.1:${VAULTIX_API_PORT:-8302}/healthz" >/dev/null
curl --fail --silent --show-error "http://127.0.0.1:${VAULTIX_WEB_PORT:-8301}/healthz" >/dev/null

echo "vaultix health checks passed"

