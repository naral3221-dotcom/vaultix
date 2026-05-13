---
project_name: Vaultix
project_type: monorepo
primary_languages: [Python, TypeScript]
tech_stack: [FastAPI, Next.js, PostgreSQL, Redis, Celery, Docker Compose, Tailwind, shadcn/ui, Auth.js v5, Alembic, SQLAlchemy]
domain: AI 생산성 에셋 허브 — 한국어 이미지 자산 카탈로그 및 자동 생성 파이프라인
schema_version: "1.0"
last_updated: 2026-05-14T04:24:07+09:00
---

# Conventions

## 네이밍

| 영역 | 규칙 |
|---|---|
| Python 패키지 | `vaultix_api` (snake_case). 인포트는 항상 이 이름으로 시작. |
| Docker 컨테이너 | `vaultix-<service>` (예: `vaultix-api`, `vaultix-postgres`) |
| Docker 네트워크 | `vaultix_internal` |
| Docker Compose project | `vaultix` |
| 호스트 데이터 경로 | `/var/lib/vaultix/<service>/...` |
| DB 이름 / 유저 | `vaultix` |
| GitHub 저장소 | `naral3221-dotcom/vaultix` |

## 디렉토리 구조

- **apps/api**: `src/vaultix_api/` 안에 모든 백엔드 코드. `tests/` 는 그 외부.
- **apps/web**: `src/app/` (App Router) 안에 라우트. 공통 컴포넌트는 `src/app/_components/`.
- **alembic**: 마이그레이션 파일은 `apps/api/alembic/versions/` 안. 새 마이그레이션은 *항상* `alembic revision --autogenerate -m "<설명>"`.

## 코딩 스타일

### Python (apps/api)

- **포맷터**: `ruff` (line-length 100, target py312)
- **타입 힌트**: 가능한 모든 곳에. `from __future__ import annotations` 권장.
- **Pydantic**: 설정은 `pydantic-settings`, API 스키마는 Pydantic v2.
- **SQLAlchemy**: 2.0 스타일 (`async`/Mapped 사용). 1.x 레거시 문법 금지.

### TypeScript (apps/web)

- **Next.js**: App Router. Pages Router 신규 도입 금지.
- **React**: Server Component 우선. `"use client"` 는 필요한 곳만.
- **테스트**: vitest + @testing-library/react. jsdom 환경.

## 테스트

- **API**: `cd apps/api && VAULTIX_ENV=test uv run pytest -q`
- **Web**: `cd apps/web && corepack pnpm test -- --run`
- **TDD 디폴트**: 의미 있는 로직 변경·새 함수·버그 수정은 RED → GREEN → REFACTOR. 면제: 오타·문구, 설정값/환경변수, 문서(`.md`), 순수 스타일/CSS, UI 텍스트만.
- **커버리지**: 80%+. 금융/인증/보안은 100%.

## 커밋

- **형식**: `<type>: <description>` — type ∈ {feat, fix, refactor, docs, test, chore, perf, ci}
- **예시** (실제 history):
  - `feat: generate asset webp derivatives`
  - `feat: add admin bulk asset import`
  - `feat: use openai image generation provider`
- **PR 분석**: 마지막 커밋이 아니라 *전체 커밋 히스토리* 를 본다 (`git diff [base]...HEAD`).

## Git Remote

- **`origin` = vault** (디폴트). URL: `http://100.116.156.37:9006/jh97/vaultix.git`. Tailscale 안에서만 접근 가능 (외부 노출 0).
- **`github` = 백업** (강등). URL: `git@github.com:naral3221-dotcom/vaultix.git`. 거의 사용 안 함. 명시 요청 시에만 `git push github main`.
- **새 커밋의 디폴트 push 대상 = vault**. 코드 변경 후 `git push` 만 입력하면 vault 로 감.
- **재해 복구 (vault 장애 시)**: forge setup 스크립트로 자동 미러 cron (`매일 04:13 vault → github`) 설치 가능. 글로벌 룰 `rules/vault.md` 참조.
- **vault repo 자동 생성**: 첫 push 시 Gitea 가 없는 repo 를 자동 생성 (private 기본). 본 프로젝트는 이미 생성됨 (`9bff8b3` 커밋 push 완료).
- **인증**: `credential.helper = store` 로 `~/.git-credentials` 에 자격 저장. PAT 권장 (Gitea 웹 UI 의 `user/settings/applications` 에서 발급).

## 버전 (Versioning)

- **단일 진실 공급원**: 모노레포 루트 `VERSION` 파일.
- **동기화 대상**: `apps/api/pyproject.toml` 의 `version`, `apps/web/package.json` 의 `version`. 셋이 항상 같아야 함.
- **현재**: `0.1.0` (Pre-MVP).
- **bump 시점**: MVP (Phase 0 + Phase 1) 완료 → `1.0.0`. 그 전까지 `0.x.y` 유지.
- **버전 bump 절차**: 루트 `VERSION` 수정 → `pyproject.toml` / `package.json` 동기화 → 커밋 메시지에 `chore(release): bump VERSION to X.Y.Z`.

## 환경 변수

- **`.env`** 는 절대 커밋 금지. **`.env.example`** 만 커밋.
- 비밀값 패턴 (`sk-`, `pk-`, `xoxb-`, etc.) 은 코드/로그/메모리 어디에도 박지 않는다.
- 모든 변수 사용 시 `if (!value) throw` 패턴으로 누락 즉시 실패.

## LLM 호출

- **반드시 OpenClaw Gateway 경유**. `anthropic`/`openai`/`google-genai` SDK 직접 임포트 금지 (글로벌 룰 `openclaw-priority.md`).
- A7 정책의 `task_type` → provider/model 매핑은 *의도* 만 규정. 실제 호출은 OpenClaw 가 통제.
- 모든 호출은 `llm_call_log` 테이블에 기록.

## 이미지 처리

- **파일 저장 경로**: `/var/lib/vaultix/assets/{yyyy}/{mm}/{dd}/{uuid}.{ext}`
- **포맷**: 원본 PNG, 파생물 WebP. JPEG 사용 안 함 (Vaultix 컨벤션).
- **체크섬**: SHA-256, 별도 컬럼 (`asset_files.sha256`). cron 검증.
- **EXIF**: AI 생성물임을 명시 (제공자/모델/프롬프트/생성 시각).
- **WebP 품질**: 80~85 (시각 검토 결과 따라 조정). 다운로드 최적화용.

## 다운로드

- **signed URL + Redis nonce** (1회 사용). Redis TTL 60초.
- **시간당 30회 rate limit** (IP + 사용자 ID 키).
- **이메일 인증 전 다운로드 제한** (계정 1개당 1회 미만).
- **Turnstile** 검증 → 통과 시 X-Accel-Redirect 로 nginx 가 직접 파일 서빙.
- **카운트 기준**: 다운로드 *완료* (HTTP 200 + 클라이언트 완료 신호) 만 집계.

## 로깅 및 감사

- **에러**: Sentry 로 전송. 운영자 알림은 P0~P2 분류.
- **감사 로그**: 어드민 액션 (asset 발행/takedown, report 처리, panic 토글) 은 `audit_log` 테이블에 기록.
- **공개 활동 로그**: `/log` 페이지에 일부 노출 (투명성).

## Phase 진척 추적

- **단일 진실 공급원**: `docs/ROADMAP.md`. 다른 곳에 진척 표기 두지 않는다.
- 새 작업 시작 전 ROADMAP 확인. 완료 시 ROADMAP 업데이트.

## 작업 시작 시 자기 분류

(코딩-style 룰)

작업 받으면 한 줄로 분류 선언:
- "TDD로 진행합니다" → `/tdd` 사이클
- "면제 케이스 (사유), 바로 진행" → 직접 수정

## 인간-시간 견적 금지

(Golden Principle #14)

계획·견적·진척 보고에서 시간 단위 (시간/일/주) 견적 금지. 허용: High/Medium/Low 정성 라벨, Phase 1/2/3 단계 구분.

## Phase Atomicity

(Golden Principle #15)

사용자가 "Phase A 진행" 라 하면 Phase A 전체를 한 단위로 처리. 하위 단계 (A-1/A-2) 사이의 *중간 확인* 금지. 멈춰도 되는 케이스 세 가지만:
1. 진짜 블로커 (파일 없음, 명령 실패, 의존성 미설치)
2. 제품/기획 결정 발생 (vibe-coder-profile *사용자 질문* 카테고리)
3. 되돌리기 어려운 작업 (DB 마이그레이션 *실행*, 외부 API 호출, 파괴적 git, 프로덕션 영향)
