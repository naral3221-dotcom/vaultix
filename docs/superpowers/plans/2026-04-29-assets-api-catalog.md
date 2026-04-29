# Assets API Catalog Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the first DB-backed public catalog API for Phase 1 image assets.

**Architecture:** Add FastAPI database dependencies, response serializers, public meta/assets routers, and a deterministic demo seed command. Keep search/cursor simple for this slice while preserving A2-compatible response envelopes.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic-style dict serializers, PostgreSQL 17, pytest.

---

## Chunk 1: Public Catalog API

### Task 1: API Contract Tests

**Files:**
- Create: `apps/api/tests/test_public_catalog_api.py`

- [ ] **Step 1: Write failing tests for `/api/v1/meta/categories`, `/api/v1/meta/tags`, `/api/v1/assets`, and `/api/v1/assets/{slug}`**
- [ ] **Step 2: Implement routers and serializers**
- [ ] **Step 3: Add demo seed command**
- [ ] **Step 4: Run API tests, seed VPS DB, verify Tailscale endpoints**
