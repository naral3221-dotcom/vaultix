---
project_name: Vaultix
project_type: monorepo
primary_languages: [Python, TypeScript]
tech_stack: [FastAPI, Next.js, PostgreSQL, Redis, Celery, Docker Compose, Tailwind, shadcn/ui, Auth.js v5, Alembic, SQLAlchemy]
domain: AI 생산성 에셋 허브 — 한국어 이미지 자산 카탈로그 및 자동 생성 파이프라인
schema_version: "1.0"
last_updated: 2026-05-14T04:24:07+09:00
---

# Dependencies

## 외부 서비스 (운영 의존성)

### LLM 제공자 (4사, A7 정책)

| 회사 | 모델 (2026-04-28 기준) | 호출 경로 | 보유 키 |
|---|---|---|---|
| Anthropic | Claude Opus 4.6 / Sonnet 4.6 | **OpenClaw Gateway** (anthropic provider, OAuth token 모드 — Claude Max 구독 풀) | ✅ 무제한 |
| OpenAI | GPT-5 (또는 시점 플래그십) + `gpt-image-2` | **OpenClaw Gateway** (api_key 모드) | ✅ 무제한 |
| Google AI | Gemini 2.5 Pro | **OpenClaw Gateway** (api_key 모드) | ✅ 무제한 |
| Z.AI | GLM 4.6 | **OpenClaw Gateway** | ✅ 무제한 |

**핵심 규칙**: 이 VPS 환경에서 *모든 LLM 호출은 OpenClaw 경유*. `anthropic` / `openai` / `google-genai` SDK 직접 임포트 금지. OpenClaw 가 per-agent 라우팅·rate limit·풀 분리를 통제. 자세히는 `/home/openclaw/claude-forge/rules/openclaw-priority.md`.

### 이미지 생성 (3티어, D-1)

| 순위 | 제공자 | 용도 | 가용성 |
|---|---|---|---|
| 1차 | **Nanobanana API** | 일반 이미지 대량 생성 | 항시 |
| 2차 | **OpenAI `gpt-image-2`** | 1차 실패/품질미달 시 폴백 | 항시 |
| 3차 | **데스크탑 ComfyUI** | ControlNet/LoRA/캐릭터 일관성 특수 워크플로우 | 평일 22~08, 주말. Tailscale 연결 |

### 임베딩

- **sentence-transformers (로컬, CPU)** — `paraphrase-multilingual-MiniLM-L12-v2` (384d, ~100MB). API 비용 회피.

### 트랜잭션 이메일

- **Resend** — 회원 가입 인증, 비밀번호 재설정.

### Abuse 방지

- **Cloudflare Turnstile** — 다운로드 시 봇 차단.
- **Redis nonce** — signed URL 단발 사용 보장.
- **이메일 인증 전 다운로드 제한** — 1회 미만으로 제한.
- **시간당 30회 rate limit**.

### 분석·모니터링

| 도구 | 용도 |
|---|---|
| **Sentry** | 에러 추적 (목표: 0.5% 미만) |
| **Uptime Kuma** | 외부 헬스 모니터 (목표: 99%+) |
| **Plausible** | 사용자 분석 (Phase 4) |
| **Listmonk** | 뉴스레터 (`/newsletter`) |

### 인프라

- **PostgreSQL 17** — 운영 DB. Alembic 마이그레이션.
- **Redis** — 세션·rate limit·signed URL nonce·Celery broker.
- **Tailscale** — VPS ↔ 데스크탑 ComfyUI 연결, 어드민 노출.
- **nginx** (시스템 레벨) — reverse proxy + X-Accel-Redirect 다운로드.
- **GitHub Actions** — CI/CD.
- **pgBackRest 또는 wal-g** — WAL 백업 (RPO 1h / RTO 4h).

## Python 의존성 (`apps/api/pyproject.toml`)

- `fastapi >= 0.115`
- `uvicorn[standard] >= 0.34`
- `sqlalchemy >= 2.0`
- `alembic >= 1.16`
- `psycopg[binary] >= 3.2`
- `redis >= 7.4`
- `pillow >= 12.2` (이미지 처리, EXIF, WebP)
- `pydantic-settings >= 2.8`
- `httpx >= 0.28`

**Dev**: `pytest >= 8.3`, `ruff >= 0.9`.
**Python 패키지 매니저**: `uv`. (pip 직접 사용 지양.)

## TypeScript 의존성 (`apps/web/package.json`)

- `next ^14.2.28` + `@next/env`
- `react ^18.3.1` + `react-dom ^18.3.1`

**Dev**: `vitest ^3.1`, `@testing-library/react ^16.3`, `@testing-library/jest-dom ^6.6`, `jsdom ^26.1`, `@vitejs/plugin-react ^4.4`, `typescript ^5.8.3`.

**Web 패키지 매니저**: pnpm@10.33.2 (corepack 으로 고정).

## 폐기된 의존성 (역사 — 다시 추가하지 말 것)

| 폐기 | 이유 | 대체 |
|---|---|---|
| Ollama 컨테이너 (Qwen 2.5 7B/14B) | 4사 무제한 키 보유, VPS CPU 보존, 자체 호스팅 복잡도 회피 | A7 외부 API 라우팅 |
| Replicate API | 더 나은 1차/2차 이미지 라인 (Nanobanana + gpt-image-2) | 라인업 제외 |
| fal.ai | 동일 사유 | 라인업 제외 |
| ComfyUI 1차 메인 운영 | 데스크탑 항시 가동 불가 | 특수 워크플로우 전용 (A7 §4.3) |
| Claude Haiku 월 $5 한도 | 비용 무관 (무제한 키) | Sonnet/Opus 4.6 |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, Ollama Docker service | 위 사유 | 환경 변수 자체를 만들지 않음 |
| 로컬 GGUF 모델 (`C:\AI\llm` Qwen3.6) MVP 기본 라우팅 | MVP 단순화 | 보조/실험용 (D-21). 향후 결정 시 `LOCAL_LLM_BASE_URL` OpenAI-compatible endpoint 신설 |

## 환경 변수 (`.env.example` 참고)

- `DATABASE_URL` (psycopg 형식)
- `REDIS_URL`
- `OPENAI_API_KEY` (Phase 3 마일스톤: 프로덕션 설정 + 저장 확인)
- `OPENAI_IMAGE_MODEL=gpt-image-2` (고정)
- `NANOBANANA_API_KEY`
- `RESEND_API_KEY`
- `TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY`
- `ADMIN_EMAILS` (어드민 권한 부여)
- `TAILSCALE_*` (ComfyUI 연결 시)
- `VAULTIX_ENV` (`test` / `dev` / `prod`)

> 비밀 변수의 *값* 은 `.agent/` 에 기록하지 않음. `state.md` / `log.md` 에도 절대 박지 않음. 패턴 (예: `sk-...`) 발견 시 즉시 제외.
