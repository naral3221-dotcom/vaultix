#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../../apps/api"
uv run alembic upgrade head
