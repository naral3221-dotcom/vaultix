---
project_name: Vaultix
project_type: monorepo
primary_languages: [Python, TypeScript]
tech_stack: [FastAPI, Next.js, PostgreSQL, Redis, Celery, Docker Compose, Tailwind, shadcn/ui, Auth.js v5, Alembic, SQLAlchemy]
domain: AI 생산성 에셋 허브 — 한국어 이미지 자산 카탈로그 및 자동 생성 파이프라인
schema_version: "1.0"
last_updated: 2026-05-14T04:24:07+09:00
---

# Architecture

## 모노레포 레이아웃

```
vaultix/
├── apps/
│   ├── api/                  # FastAPI 백엔드 (Python 3.12+, uv)
│   │   ├── src/vaultix_api/  # 패키지명 (Docker/Python 식별자 통일)
│   │   ├── alembic/          # DB 마이그레이션 (versions/)
│   │   ├── tests/            # pytest
│   │   └── pyproject.toml    # hatchling + ruff(line-length 100, py312)
│   └── web/                  # Next.js 14 (App Router, TypeScript)
│       ├── src/app/          # 라우트 (asset, healthz, newsletter, _components)
│       ├── src/test/         # vitest + jsdom
│       └── package.json      # pnpm@10.33.2, next@14.2.x, react@18.3
├── infra/
│   ├── docker-compose.yml    # 메인 스택
│   ├── docker-compose.dev.yml
│   ├── nginx/                # 시스템 nginx server block
│   └── scripts/              # healthcheck 등
├── docs/
│   ├── ROADMAP.md            # Phase 상태 추적 (단일 진실 공급원)
│   └── superpowers/
├── 기획서/                    # 23개 한국어 기획 문서 (구현 기준)
├── .agent/                   # ← 이 메모리 인프라
├── .env.example              # 환경 변수 템플릿
├── .editorconfig
├── .github/                  # CI/CD (GitHub Actions)
└── README.md
```

## 런타임 구성 (개발 로컬)

| 컴포넌트 | 호스트 포트 | 컨테이너 prefix | 비고 |
|---|---|---|---|
| Web (Next.js) | `127.0.0.1:8301` | `vaultix-web` | `next dev -H 0.0.0.0 -p 3000` 내부 |
| API (FastAPI) | `127.0.0.1:8302` | `vaultix-api` | `uvicorn` |
| PostgreSQL 17 | `127.0.0.1:5440` | `vaultix-postgres` | DB: `vaultix`, user: `vaultix` |
| Redis | `127.0.0.1:6380` | `vaultix-redis` | 세션/큐/rate limit |
| Celery worker | — | `vaultix-celery` | 비동기 잡 |
| Celery beat | — | `vaultix-celery-beat` | 스케줄러 |
| Plausible | — | `vaultix-plausible` | 분석 (Phase 4) |
| Uptime Kuma | — | `vaultix-uptime` | 외부 헬스 모니터 |
| Listmonk | — | `vaultix-listmonk` | 뉴스레터 (`/newsletter`) |

- **네트워크**: `vaultix_internal` (단일 Docker network)
- **데이터 영속**: `/var/lib/vaultix/...` (호스트 마운트)
- **노출**: 시스템 nginx 가 reverse proxy. Admin 은 Tailscale 전용 노출.

## 데이터 흐름 (Phase 1+3 기준)

### 1. 공개 탐색 / 다운로드

```
사용자 → nginx → Next.js (SSR/ISR)
              → /api → FastAPI → Postgres (assets, categories, tags, asset_files)
                                → Redis (rate limit, signed URL nonce)
              → 다운로드: signed URL + Redis nonce + X-Accel-Redirect
                  + Turnstile + 이메일 인증 + 시간당 30회 제한
```

### 2. 자동 이미지 생성 파이프라인

```
generation_jobs (대기)
  ↓ Celery worker
  ↓
[1차] Nanobanana API 호출
  ↓ 실패/품질미달 시 자동 승격
[2차] OpenAI gpt-image-2
  ↓ 특수 워크플로우 (ControlNet/LoRA/시리즈) 필요 시
[3차] ComfyUI (데스크탑, Tailscale, 가용 시간만)
  ↓
이미지 검증 → 점수화 (CLIP) → 썸네일/WebP 파생물 생성 → SHA-256 체크섬
  ↓
LLM 라우터 (A7 정책) → 제목·설명·alt·tag·카테고리 자동 생성
  ↓
asset_inbox 적재 → 어드민 검수 → publish → 공개 카탈로그
```

### 3. LLM 라우팅 (A7)

| 작업 | 1차 모델 | 폴백 |
|---|---|---|
| 자산 메타데이터 (제목/설명/alt) | Gemini 2.5 Pro | GPT-5 |
| 카테고리·태그 분류 | GLM 4.6 | Gemini 2.5 Pro |
| 신고/abuse 분류 | GPT-5 | Gemini 2.5 Pro |
| 번역(Phase 2+) | Claude Sonnet 4.6 | GPT-5 |
| 블로그 초안(Phase 3+) | Claude Opus 4.6 | GPT-5 |
| 인사이트 통합(Phase 3+) | Claude Opus 4.6 | — |
| 토픽 점수화 | Gemini 2.5 Pro | GLM 4.6 |
| 임베딩 | sentence-transformers 로컬 (paraphrase-multilingual-MiniLM-L12-v2, 384d) | — |

- 모든 호출은 단일 진입점 (`backend/llm_router.py`) 통과.
- **글로벌 룰**: 본 환경(VPS)에서 모든 LLM 호출은 **OpenClaw Gateway 경유** 강제 (`anthropic` / `openai` / `google-genai` SDK 직접 임포트 금지). A7 정책은 라우팅 *의도* 를 규정, OpenClaw 가 *실제 실행* 을 통제.
- 모든 호출은 `llm_call_log` 테이블에 기록 (provider, model, tokens, latency, success/failover).

## 인증 및 세션

- **Auth.js v5** (Next.js 측) + FastAPI 세션 미들웨어 (DB 세션 검증).
- 테이블: `users`, `sessions`, `email_verifications`, `password_resets`.
- 이메일: Resend (transactional). Phase 2 에서 Google OAuth 연결 완료.

## 운영 가시성

- **`/admin/panic`**: 사이트 긴급 점등/소등 토글.
- **`/admin/inbox`**: 큐레이션.
- **`/admin/dashboard`**: 자산/LLM 호출/실패율/체크섬 위젯.
- **`/admin/takedowns`**, **`/admin/log/{date}`**: 감사 로그.
- **`/report`**: 공개 신고 접수 → GPT-5 자동 분류 → 어드민 큐.
- **Sentry** (에러), **Uptime Kuma** (외부 헬스), **Plausible** (분석, Phase 4).

## 백업 및 안정성

- **pgBackRest 또는 wal-g**: WAL 백업, RPO 1h / RTO 4h.
- **자산 체크섬**: SHA-256 cron 검증.
- **이미지 워커**: 데스크탑 ComfyUI 가용 시간대 (평일 22~08, 주말) 만 큐잉. Tailscale 으로 VPS↔데스크탑 연결.
