---
project_name: Vaultix
project_type: monorepo
primary_languages: [Python, TypeScript]
tech_stack: [FastAPI, Next.js, PostgreSQL, Redis, Celery, Docker Compose, Tailwind, shadcn/ui, Auth.js v5, Alembic, SQLAlchemy]
domain: AI 생산성 에셋 허브 — 한국어 이미지 자산 카탈로그 및 자동 생성 파이프라인
schema_version: "1.0"
last_updated: 2026-05-14T04:24:07+09:00
---

# Overview

## 한 줄 정의

**Vaultix** 는 한국어 사용자를 위한 AI 생산성 에셋 (이미지 우선) 카탈로그 + 자동 생성 + 다운로드 사이트.

## 왜 존재하는가

- **운영자(JH)** 가 본업 광고/마케팅 1인 운영자이면서, AI 콘텐츠 허브를 부업/장기 자산으로 구축.
- 시장 빈틈: 한국어 페르소나용 무료 고품질 이미지 자산이 부족. 영어권 사이트는 한국 페르소나·시나리오 부재.
- 외부 LLM/이미지 API 무제한 키 보유 → 자체 호스팅 부담 없이 *대량 자동 생성 + 큐레이션* 전략.

## 핵심 사용 시나리오

| 사용자 | 흐름 |
|---|---|
| 일반 사용자 | 가입 → 이메일 인증 → 카탈로그 탐색 → 자산 상세 → 다운로드 (시간당 30회 제한, Turnstile) |
| 관리자(JH) | `/admin/inbox` 에서 자동 생성 자산 검수 → 메타데이터 편집 → 발행 → `/today` 큐레이션 별표 |
| 자동 워커 | Nanobanana → 폴백 시 `gpt-image-2` → 특수 케이스 ComfyUI → 검증·점수화 → 썸네일/WebP 파생물 생성 → 인박스 적재 |

## 현재 상태 (2026-05-14 기준)

- **Phase 3 (이미지 공급 파이프라인)** Active, 85%.
- Phase 0 / 1 / 2 완료: VPS·Docker·Postgres·Redis 베이스라인, 공개 카탈로그·계정 흐름·다운로드·신고, 어드민 운영·감사 로그·OAuth·생성 큐 MVP.
- 진행 중: 프로덕션 `OPENAI_API_KEY` 설정 + 생성 자산 저장 확인.
- 다음: 프롬프트 템플릿·결과 검수, 카탈로그 발견성 개선, 비동기 워커 분리.

## 최근 변경 (commit 기준 최신 → 과거)

| 커밋 | 요약 |
|---|---|
| `33f03a8` | feat: generate asset webp derivatives |
| `1ed666a` | feat: add admin bulk asset import |
| `c58f25f` | feat: add admin asset metadata editing |
| `62f6044` | feat: use openai image generation provider |
| `87bf4f4` | feat: connect generation queue worker |
| `73796f2` | feat: add admin generation request queue |
| `20fd38c` | feat: add google oauth login |
| `131958c` | feat: add development roadmap view |
| `69e16d0` | feat: add report resolution and audit log view |
| `c6a62d8` | feat: add admin review workspace |

## Phase 의존성

```
Phase 0 ── Phase 1 ── Phase 2 ── Phase 3 ── Phase 4 ── Phase 5
  ✅         ✅         ✅         🟡           ⚪          ⚪
                                  (85%)
```

(Phase 4 = SEO/Analytics/Monitoring/Backups. Phase 5 = 차별화/영상)

## MVP 완료 조건 (참고)

- 베타 5명: 가입→인증→탐색→다운로드 완료
- 일 자동 생성 50장 이상 7일 연속
- Nanobanana 비중 80%+, gpt-image-2 폴백 20% 이하, ComfyUI 일반 0%
- 인박스 30분에 50장 처리 가능
- `/admin/panic` 검증, `/report` 시뮬레이션, 백업 리허설, Sentry 0.5% 미만, Uptime 99%+
