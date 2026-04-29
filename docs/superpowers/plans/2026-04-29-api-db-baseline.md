# API DB Baseline Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first SQLAlchemy and Alembic baseline for Vaultix API.

**Architecture:** Keep database setup focused on model metadata and migration scaffolding. Define core Phase 1 tables from A1 at a minimal schema level, wire Alembic to the same metadata, and leave live PostgreSQL integration for the next infrastructure slice.

**Tech Stack:** Python 3.12, SQLAlchemy 2.0, Alembic, pytest, uv.

---

## Chunk 1: API Database Baseline

### Task 1: Metadata and Migration Scaffold

**Files:**
- Modify: `apps/api/pyproject.toml`
- Modify: `apps/api/src/vaultix_api/settings.py`
- Create: `apps/api/src/vaultix_api/db/base.py`
- Create: `apps/api/src/vaultix_api/models/core.py`
- Create: `apps/api/alembic.ini`
- Create: `apps/api/alembic/env.py`
- Create: `apps/api/alembic/versions/0001_init_users_assets.py`
- Create: `apps/api/tests/test_db_metadata.py`

- [ ] **Step 1: Write failing tests for expected tables and Alembic files**

Run: `cd apps/api && VAULTIX_ENV=test uv run pytest tests/test_db_metadata.py -q`
Expected: FAIL because `vaultix_api.db` and models do not exist.

- [ ] **Step 2: Add SQLAlchemy dependencies and model metadata**

Create a declarative base, model classes for `users`, `sessions`, `categories`, `tags`, `assets`, `asset_files`, and `asset_tags`, and settings for `DATABASE_URL`.

- [ ] **Step 3: Add Alembic scaffold**

Wire Alembic `target_metadata` to the same SQLAlchemy metadata and add revision `0001_init_users_assets.py`.

- [ ] **Step 4: Verify API tests**

Run: `cd apps/api && VAULTIX_ENV=test uv run pytest -q`
Expected: PASS.
