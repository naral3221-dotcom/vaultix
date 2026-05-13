---
project_name: Vaultix
project_type: monorepo
primary_languages: [Python, TypeScript]
tech_stack: [FastAPI, Next.js, PostgreSQL, Redis, Celery, Docker Compose, Tailwind, shadcn/ui, Auth.js v5, Alembic, SQLAlchemy]
domain: AI 생산성 에셋 허브 — 한국어 이미지 자산 카탈로그 및 자동 생성 파이프라인
schema_version: "1.0"
last_updated: 2026-05-14T04:24:07+09:00
---

# Decisions

> 영속 결정 레지스트리. 원본은 `기획서/00_확정사항_레지스트리.md`. 본 페이지는 *구현 에이전트가 자주 참조해야 할* 결정만 발췌·압축. 충돌 시 원본 우선.

## 프로젝트 정체성

| ID | 결정 | 일자 |
|---|---|---|
| Brand | 최종 프로젝트명 **Vaultix**. 이전 명칭 (`image-web-project`, "AI 콘텐츠 허브") 은 역사 문서. | 2026-04-29 |
| Identifier | 코드/인프라 식별자 = `vaultix`. Python 패키지명 = `vaultix_api`. Docker prefix = `vaultix-`. Network = `vaultix_internal`. 호스트 경로 = `/var/lib/vaultix/...`. | 2026-04-29 |
| Remote-Default | **`origin` = vault** (`http://100.116.156.37:9006/jh97/vaultix.git`, self-hosted Gitea on Tailscale). GitHub 은 `github` remote 로 백업·강등. 모든 `git push` 의 디폴트 = vault. 사용자 명시 ("왠만해서는 깃허브 안 쓸 거"). 자동 미러 cron 은 forge setup 으로 별도 설치 가능. | 2026-05-14 |
| Versioning | 모노레포 루트 `VERSION` 파일이 단일 진실 공급원. `apps/api/pyproject.toml` 과 `apps/web/package.json` 의 `version` 은 이 값과 동기화. 현재 = `0.1.0`. MVP 완료 시 `1.0.0` bump. | 2026-05-14 |

## 범위 (Scope)

| ID | 결정 | 영향 |
|---|---|---|
| MVP-Scope | MVP = Phase 0 + Phase 1 *만*. 한국어 이미지 자산 사이트 한정. | PPT/SVG/DOCX, 다국어, OAuth, AdSense, 블로그 자동화 모두 MVP 외 |
| Doc-Priority | 문서 충돌 시 우선순위: `00_IMPLEMENTATION_SPEC_v0.4.md` > 확정 레지스트리 > A7 > A1/A2 > B1/B2 > Phase 0/1. 역사 문서 (`AI컨텐츠허브_기획안_v0.3.md`, `99_최종검토_정합성보고서.md`) 는 구현 기준 *아님*. | 모든 코딩 결정의 1차 참조처 |

## LLM 및 이미지

| ID | 결정 | 이유 |
|---|---|---|
| D-13 | Ollama 컨테이너 폐기. Anthropic/OpenAI/Google AI/Z.AI 외부 API 라우팅. | 4사 무제한 키 보유, VPS CPU 보존 |
| D-14 | 이미지 라인업: Nanobanana → `gpt-image-2` → ComfyUI 특수 워크플로우 (3티어). Replicate / fal.ai 폐기. | Nanobanana + gpt-image-2 가 더 나은 1·2차. ComfyUI 는 데스크탑 항시 가동 불가. |
| D-15 | 모든 LLM 호출은 단일 라우팅 레이어 (`backend/llm_router.py`) 통과. `llm_call_log` 에 기록. | 모델 교체·A/B·로깅 일원화 |
| D-21 | 로컬 GGUF 모델 (`C:\AI\llm` Qwen3.6) 은 MVP 기본 라우팅에 *포함하지 않음*. LM Studio/llama.cpp 계열 보조/실험용. | MVP 복잡도 최소화. 향후 필요 시 `LOCAL_LLM_BASE_URL` OpenAI-compatible endpoint 신설 |
| 환경 룰 | 본 VPS 모든 LLM 호출은 **OpenClaw Gateway 경유** 강제. `anthropic`/`openai`/`google-genai` SDK 직접 임포트 금지. | per-agent 라우팅·rate limit·풀 분리. 2026-04-15 사고 (plasys-sync cron 이 Claude Max 풀 소진) 의 교훈 |

## 비용·운영

| ID | 결정 | 이유 |
|---|---|---|
| Cost-Policy | 무제한 키 보유 전제. *비용 캡* 보다 *호출량/장애/도용 감시* 우선. 호출 비용 추정은 참고용으로만 기록. | JH 환경 |
| Embedding | 임베딩은 sentence-transformers 로컬 (paraphrase-multilingual-MiniLM-L12-v2, 384d). API 호출 안 함. | 가벼움 + 비용 누적 회피 |
| Backup | pgBackRest 또는 wal-g 기반 WAL 백업. RPO 1h / RTO 4h. | A6 운영 런북 기준 |
| Image-Routing-Promotion | 자동 승격 조건: 5xx / NSFW 필터 탈락 / CLIP score 임계 미달 / 같은 프롬프트 패턴의 신고 누적. | A7 §4.2 |

## DB·아키텍처

| ID | 결정 | 이유 |
|---|---|---|
| DB | PostgreSQL 17. (다른 버전 가정 금지.) | A1 DDL 기준 |
| Monorepo | apps/api + apps/web + infra 의 단일 저장소. | A1/A2 통합 흐름 |
| Auth | Auth.js v5 + FastAPI 세션 미들웨어 (DB 세션 검증). | Phase 2 에서 Google OAuth 연결 완료 |

## 다국어 (i18n)

| ID | 결정 |
|---|---|
| MVP | 한국어만 |
| Post-MVP | 일본어 우선 → 영어는 이후 |

## 콘텐츠 신뢰

| ID | 결정 |
|---|---|
| AI-Provenance | EXIF + HTML meta 로 AI 생성물 명시 (MVP). |
| C2PA | C2PA 실제 서명은 MVP 외. 후속 배포에서 검토. |

## 보안

| ID | 결정 |
|---|---|
| Download-Limit | signed URL + Redis nonce + Turnstile + 이메일 인증 전 제한 + 시간당 30회. |
| Admin-Exposure | 어드민은 Tailscale 전용 노출. 공개 인터넷 노출 금지. |

## 자동 결정 정책 (구현 에이전트)

Vibe-coder-profile 기준 — 사용자(JH) 에게 *질문 금지* 인 결정:
- 알고리즘/자료구조 선택
- 에러 처리 전략, 로깅
- 디자인 패턴, 아키텍처 구조
- 코드 분리/추상화 수준
- 라이브러리 API 사용법
- 리팩토링 방식, 테스트 작성 방식
- 성능 최적화

사용자에게 질문 = *기획/제품/UX* 만:
- 사용자 흐름 분기 (A vs B 흐름)
- 버튼/페이지 배치
- 기능 범위 결정
- 에러 메시지 카피

---

## 결정 추가 형식

새 결정 추가 시 위 표 중 가장 가까운 영역에 한 줄. 형식:

```
| <ID 또는 일자> | <결정 한 줄> | <이유 또는 영향> |
```

영구성 증명되기 전 (이번 세션·이번 Phase 한정) 결정은 `state.md` 의 "중요 결정" 에 임시로 두고, 영속성이 확인되면 본 페이지로 *승격*.
