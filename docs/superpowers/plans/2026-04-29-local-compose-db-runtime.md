# Local Compose DB Runtime Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Sprint 0 stack runnable locally with Postgres, Redis, API, Web, and Alembic migration support.

**Architecture:** Keep production compose defaults aligned with `/var/lib/vaultix`, and add a development override using named Docker volumes so local runs do not require host `/var/lib` permissions. Add a small DB runtime module for SQLAlchemy engine/session construction and a migration helper script for local and deployment usage.

**Tech Stack:** Docker Compose, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 17, Redis 7.

---

## Chunk 1: Runtime DB and Compose Dev

### Task 1: DB Runtime Utilities

**Files:**
- Create: `apps/api/src/vaultix_api/db/session.py`
- Create: `apps/api/tests/test_db_session.py`

- [ ] **Step 1: Write failing tests**
- [ ] **Step 2: Implement engine/session helpers**
- [ ] **Step 3: Verify API tests**

### Task 2: Compose Runtime

**Files:**
- Create: `infra/docker-compose.dev.yml`
- Create: `infra/scripts/migrate.sh`
- Modify: `README.md`

- [ ] **Step 1: Add dev override with named volumes**
- [ ] **Step 2: Add migration helper**
- [ ] **Step 3: Verify compose config, containers, migration, and health checks**
