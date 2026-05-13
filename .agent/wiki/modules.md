---
project_name: Vaultix
project_type: monorepo
primary_languages: [Python, TypeScript]
tech_stack: [FastAPI, Next.js, PostgreSQL, Redis, Celery, Docker Compose, Tailwind, shadcn/ui, Auth.js v5, Alembic, SQLAlchemy]
domain: AI 생산성 에셋 허브 — 한국어 이미지 자산 카탈로그 및 자동 생성 파이프라인
schema_version: "1.0"
last_updated: 2026-05-14T04:24:07+09:00
---

# Modules

3개 최상위 모듈. 각각 독립 배포 가능.

## `apps/api` — FastAPI 백엔드

| 항목 | 값 |
|---|---|
| 언어 | Python 3.12+ |
| 패키지 매니저 | `uv` |
| 패키지명 | `vaultix_api` (Python import 경로) |
| 빌드 | hatchling |
| 린터 | ruff (line-length 100, target py312) |
| 테스트 | pytest (`uv run pytest -q`) |
| 서버 | uvicorn (`uvicorn vaultix_api.main:app --reload`) |

**책임**:
- REST API (A2 스펙)
- 인증/세션 (Auth.js v5 호환 DB 세션 검증)
- DB 모델·마이그레이션 (SQLAlchemy + Alembic)
- 이미지 처리 (Pillow 12.2+: 썸네일·WebP 파생물·EXIF/체크섬)
- Redis 상호작용 (세션·rate limit·signed URL nonce)
- LLM 라우터 (`A7_LLM_라우팅_정책.md` 구현. *호출은 OpenClaw 경유*)
- Celery 워커 (이미지 생성 큐)
- 신호/abuse 분류 (GPT-5)
- 어드민 엔드포인트 (`/admin/inbox`, `/admin/dashboard`, `/admin/panic`, `/admin/takedowns`, `/admin/log/{date}`)

**환경 변수 (테스트)**: `VAULTIX_ENV=test`
**테스트 실행**: `cd apps/api && VAULTIX_ENV=test uv run pytest -q`

## `apps/web` — Next.js 14 프론트엔드

| 항목 | 값 |
|---|---|
| 언어 | TypeScript 5.8 |
| 패키지 매니저 | pnpm@10.33.2 (corepack) |
| 프레임워크 | Next.js 14.2 (App Router) |
| UI | Tailwind + shadcn/ui (App Router 기반) |
| 테스트 | vitest + @testing-library/react + jsdom |
| 인증 | Auth.js v5 |

**책임**:
- 공개 페이지 (`/`, `/탐색`, `/asset/[id]`, `/today`, `/log`, `/license`, `/privacy`, `/about`, `/contact`, `/report`, `/newsletter`, `/healthz`)
- 어드민 페이지 (`/admin/...`)
- 회원가입·로그인·이메일 인증·비밀번호 재설정
- 다운로드 흐름 (signed URL 요청 → 브라우저 다운로드)
- Google OAuth (Phase 2 완료)
- robots/sitemap/image-sitemap, ImageObject JSON-LD (SEO Phase 4)

**테스트 실행**: `corepack pnpm test -- --run`
**개발 서버**: `corepack pnpm dev` (포트 3000, 외부 노출은 nginx 가 8301 으로 매핑)

## `infra` — 인프라 및 운영

| 파일 | 역할 |
|---|---|
| `infra/docker-compose.yml` | 메인 스택 정의 (api, web, postgres, redis, celery, celery-beat, plausible, uptime-kuma, listmonk) |
| `infra/docker-compose.dev.yml` | 개발 오버라이드 (포트 노출, hot reload 마운트 등) |
| `infra/nginx/` | 시스템 nginx server block (reverse proxy). Admin Tailscale 전용. |
| `infra/scripts/healthcheck.sh` | 컴포넌트 헬스 점검 스크립트 |

**유효성 검증**: `docker compose -f infra/docker-compose.yml config`

## 횡단 모듈 (개념)

- **`기획서/`** — 23개 한국어 기획 문서. *구현 진실 공급원*. 현재 코드와 충돌 시 *코드를 따른다* 가 아니라 *기획서를 따른다* — 단, 충돌 발견은 `log.md` 에 `gotcha` 로 기록.
- **`docs/ROADMAP.md`** — Phase 상태의 단일 진실 공급원. 다른 곳에 진척 표기 두지 말 것.
- **`.agent/`** — 이 메모리 인프라. AI 에이전트 (클로드/코덱스) 가 세션을 가로질러 컨텍스트를 보존.

## 모듈 간 의존성

```
infra  ──→  apps/api  ←──→  apps/web
   │           │
   │           ↓
   └──→  Postgres / Redis (Docker 네트워크)

apps/api ──→ OpenClaw Gateway ──→ Anthropic / OpenAI / Gemini / Z.AI
apps/api ──→ Nanobanana API
apps/api ──→ Resend (이메일)
apps/api ──→ Cloudflare Turnstile (abuse)
apps/api ──→ Tailscale ──→ 데스크탑 ComfyUI (특수 워크플로우만)
```

`apps/web` → `apps/api` 는 항상 *API 경유*. 직접 DB 접근 금지.
