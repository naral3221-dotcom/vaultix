---
project_name: Vaultix
project_type: monorepo
primary_languages: [Python, TypeScript]
tech_stack: [FastAPI, Next.js, PostgreSQL, Redis, Celery, Docker Compose, Tailwind, shadcn/ui, Auth.js v5, Alembic, SQLAlchemy]
domain: AI 생산성 에셋 허브 — 한국어 이미지 자산 카탈로그 및 자동 생성 파이프라인
schema_version: "1.0"
last_updated: 2026-05-14T04:24:07+09:00
---

# Glossary

> 기술 약어와 내부 용어. 비즈니스 도메인 용어는 [domain](domain.md) 참조.

## 인프라·운영

| 용어 | 의미 |
|---|---|
| **main-hub** | 프로젝트가 돌아가는 Vultr Seoul VPS. 12 vCPU, 47GB RAM, 720GB NVMe, GPU 없음. |
| **VPS** | Virtual Private Server. 본 프로젝트의 호스팅 환경. |
| **Tailscale** | VPN 메쉬. VPS ↔ 데스크탑 ComfyUI 연결, 어드민 노출. |
| **OpenClaw Gateway** | 본 VPS 내 LLM 호출 라우터. 모든 LLM 호출은 이 경유. |
| **pgBackRest / wal-g** | PostgreSQL WAL 백업 도구. 둘 중 하나 채택. RPO 1h / RTO 4h. |
| **X-Accel-Redirect** | nginx 가 백엔드 응답 헤더를 보고 파일을 직접 서빙하는 기능. 다운로드 효율 향상. |
| **Tier** (Tier1/Tier2/Tier4+) | 외부 API 의 사용량 등급. Anthropic/OpenAI 등 회사별 정의. |

## 버전 관리·CI

| 용어 | 의미 |
|---|---|
| **WBS** | Work Breakdown Structure. Phase 문서의 작업 분해. |
| **MVP** | Minimum Viable Product. 본 프로젝트 = Phase 0 + Phase 1. |
| **RPO / RTO** | Recovery Point Objective / Recovery Time Objective. 백업 복구 목표. |
| **CI/CD** | Continuous Integration / Deployment. GitHub Actions. |

## 백엔드 (Python/FastAPI)

| 용어 | 의미 |
|---|---|
| **uv** | Astral 의 Python 패키지 매니저 (pip 대체). 본 프로젝트 표준. |
| **Alembic** | SQLAlchemy 의 마이그레이션 도구. |
| **psycopg** | PostgreSQL Python 드라이버 (v3 = `psycopg[binary]`). |
| **ruff** | Python 린터/포매터. line-length 100, target py312. |
| **hatchling** | Python 빌드 백엔드. |
| **Celery** | Python 비동기 작업 큐. Redis broker. |
| **Pillow** | Python 이미지 라이브러리 (PIL fork). |
| **CLIP score** | 이미지 미적 점수 모델. 생성 결과 품질 판정. |

## 프론트엔드 (TypeScript/Next.js)

| 용어 | 의미 |
|---|---|
| **App Router** | Next.js 13+ 의 라우팅 시스템. `src/app/` 디렉토리 기반. |
| **shadcn/ui** | Radix UI + Tailwind 기반 컴포넌트 모음. |
| **vitest** | Vite 기반 테스트 러너. |
| **jsdom** | 브라우저 환경 에뮬레이션 (Node 에서). |
| **corepack** | Node 의 패키지 매니저 버전 고정 도구. pnpm 호출 시 `corepack pnpm ...`. |
| **Auth.js** | NextAuth 의 v5 이름. |

## LLM·이미지

| 용어 | 의미 |
|---|---|
| **GGUF** | Georgi Gerganov Universal Format. llama.cpp/LM Studio 의 양자화 모델 포맷. |
| **LoRA** | Low-Rank Adaptation. 스타일/캐릭터 파인튜닝 어댑터. |
| **ControlNet** | 포즈/엣지/뎁스 등 조건부 이미지 생성. |
| **CLIP** | OpenAI 의 텍스트-이미지 임베딩 모델. 미적 점수에 활용. |
| **sentence-transformers** | 문장 임베딩 라이브러리. paraphrase-multilingual-MiniLM-L12-v2 (384d) 사용. |
| **NSFW filter** | Not Safe For Work 필터. 이미지 생성 후 자동 검출. |
| **token bucket** | rate limit 알고리즘. 분당 호출 한도 관리. |
| **failover** | 1차 모델 실패 시 폴백 모델로 자동 전환. |

## DB·자산

| 용어 | 의미 |
|---|---|
| **SHA-256** | 자산 무결성 체크섬. cron 검증. |
| **signed URL** | 단발성 다운로드 URL. Redis nonce 와 결합. |
| **nonce** | Number-used-once. 한 번만 유효한 토큰. |
| **EXIF** | 이미지 파일에 박힌 메타데이터. AI 생성물 명시에 사용. |
| **C2PA** | Coalition for Content Provenance and Authenticity. 콘텐츠 출처 서명 표준. MVP 외. |
| **WebP** | 구글의 이미지 포맷. 본 프로젝트의 파생물 표준. |

## 운영자·페르소나

| 용어 | 의미 |
|---|---|
| **JH** | 운영자 이니셜. 본업 광고/마케팅 1인 운영자. |
| **D-N (D-1, D-13 ...)** | `00_확정사항_레지스트리.md` 의 결정 번호. |
| **B-N, T-N** | 동 문서의 브랜드/태스크 번호. |
| **인박스** | `/admin/inbox`. 자동 생성 자산 검수 대기열. |
| **panic** | `/admin/panic`. 사이트 긴급 점등/소등 토글. |

## 글로벌 룰 위치 (참고)

| 룰 | 위치 |
|---|---|
| Golden Principles 16개 | `/home/openclaw/claude-forge/rules/golden-principles.md` |
| 프로젝트 메모리 정책 | `/home/openclaw/claude-forge/rules/project-memory.md` |
| OpenClaw 우선 | `/home/openclaw/claude-forge/rules/openclaw-priority.md` |
| Vibe coder 프로필 | `/home/openclaw/claude-forge/rules/vibe-coder-profile.md` |
| 코딩 스타일 | `/home/openclaw/claude-forge/rules/coding-style.md` |
| Git 워크플로우 | `/home/openclaw/claude-forge/rules/git-workflow-v2.md` |
| 에이전트 오케스트레이션 | `/home/openclaw/claude-forge/rules/agents-v2.md` |
| 보안 | `/home/openclaw/claude-forge/rules/security.md` |
| 인터랙션 | `/home/openclaw/claude-forge/rules/interaction.md` |
| 날짜 계산 | `/home/openclaw/claude-forge/rules/date-calculation.md` |
| Google Drive | `/home/openclaw/claude-forge/rules/google-drive.md` |
