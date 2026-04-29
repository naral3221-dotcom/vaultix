# Sprint 0 Baseline Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first runnable Vaultix monorepo baseline for local development.

**Architecture:** Create a monorepo with `apps/api`, `apps/web`, and `infra`. The API exposes a tested FastAPI `/healthz`, the web app exposes a tested Next.js `/healthz`, and Docker Compose wires Postgres, Redis, API, Web, Celery, Celery Beat, Plausible, Uptime Kuma, and Listmonk placeholders without Ollama, Replicate, or fal.ai.

**Tech Stack:** Python 3.12, FastAPI, uv, pytest, Next.js 14, TypeScript, Tailwind, pnpm, Docker Compose, PostgreSQL 17, Redis 7.

---

## Chunk 1: Local Baseline

### Task 1: API Health Baseline

**Files:**
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/src/vaultix_api/__init__.py`
- Create: `apps/api/src/vaultix_api/main.py`
- Create: `apps/api/src/vaultix_api/settings.py`
- Create: `apps/api/tests/test_health.py`
- Create: `apps/api/Dockerfile`

- [ ] **Step 1: Write the failing API health test**

```python
from fastapi.testclient import TestClient

from vaultix_api.main import app


def test_healthz_returns_status_version_and_env():
    client = TestClient(app)

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": "0.1.0",
        "env": "test",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && uv run pytest tests/test_health.py -q`
Expected: FAIL because `vaultix_api` does not exist yet.

- [ ] **Step 3: Write minimal API implementation**

Create a FastAPI app with settings read from environment and `/healthz` returning `status`, `version`, and `env`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/api && VAULTIX_ENV=test uv run pytest tests/test_health.py -q`
Expected: PASS.

### Task 2: Web Health Baseline

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/next.config.mjs`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/src/app/layout.tsx`
- Create: `apps/web/src/app/page.tsx`
- Create: `apps/web/src/app/healthz/page.tsx`
- Create: `apps/web/src/app/healthz/page.test.tsx`
- Create: `apps/web/vitest.config.ts`
- Create: `apps/web/Dockerfile`

- [ ] **Step 1: Write the failing web health test**

Render the health page and assert it displays `Vaultix web ok`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/web && pnpm test -- --run src/app/healthz/page.test.tsx`
Expected: FAIL because the app does not exist yet.

- [ ] **Step 3: Write minimal web implementation**

Create the Next.js App Router skeleton, root page, and `/healthz` page.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/web && pnpm test -- --run src/app/healthz/page.test.tsx`
Expected: PASS.

### Task 3: Repository and Infrastructure Baseline

**Files:**
- Modify: `.gitignore`
- Create: `.editorconfig`
- Create: `.env.example`
- Create: `infra/docker-compose.yml`
- Create: `infra/nginx/vaultix.conf`
- Create: `infra/nginx/vaultix-admin.conf`
- Create: `infra/scripts/healthcheck.sh`
- Create: `.github/workflows/ci.yml`
- Create: `.github/renovate.json`
- Modify: `README.md`

- [ ] **Step 1: Add repository config**

Add editor defaults, environment template, and ignore rules for local env, Python, Node, and generated assets.

- [ ] **Step 2: Add Docker Compose baseline**

Define `vaultix_internal`, Postgres 17 on `127.0.0.1:5440`, Redis 7 on `127.0.0.1:6380`, API on `127.0.0.1:8302`, Web on `127.0.0.1:8301`, Celery, Celery Beat, Plausible, Uptime Kuma, and Listmonk.

- [ ] **Step 3: Add nginx and CI skeleton**

Add public and Tailscale-admin nginx config templates plus CI commands for API and web tests/builds.

- [ ] **Step 4: Verify full baseline**

Run:
- `cd apps/api && VAULTIX_ENV=test uv run pytest -q`
- `cd apps/web && pnpm test -- --run`
- `cd apps/web && pnpm build`
- `docker compose -f infra/docker-compose.yml config`

Expected: all commands exit 0.
