---
project_name: Vaultix
project_type: monorepo
primary_languages: [Python, TypeScript]
tech_stack: [FastAPI, Next.js, PostgreSQL, Redis, Celery, Docker Compose, Tailwind, shadcn/ui, Auth.js v5, Alembic, SQLAlchemy]
domain: AI 생산성 에셋 허브 — 한국어 이미지 자산 카탈로그 및 자동 생성 파이프라인
schema_version: "1.0"
last_updated: 2026-05-14T04:24:07+09:00
---

# Domain

> 비즈니스 도메인 용어. 기술 약어는 [glossary](glossary.md) 참조.

## 자산 (Asset)

다운로드 가능한 단위 콘텐츠. MVP 에서는 **이미지 (PNG/WebP)** 만. 향후 PPT/SVG/DOCX/XLSX/HTML 확장 여지 남김.

| 상태 | 의미 |
|---|---|
| `inbox` | 자동 생성 직후, 어드민 검수 대기 |
| `draft` | 어드민이 편집 중 (메타데이터, 카테고리, 태그) |
| `published` | 공개 카탈로그 노출, 다운로드 가능 |
| `archived` | 비공개, 사후 검토 대상 |
| `takedown` | 신고/저작권 등으로 즉시 비공개 |

## 자산 파일 (Asset File)

자산 1개 = 원본 + 파생물 N개. 한 자산이 여러 해상도/포맷의 파일을 보유:

- 원본 (생성 시 받은 PNG)
- 썸네일 (작은 PNG)
- WebP 파생물 (다운로드 최적화)

## 큐레이션 인박스 (Curation Inbox)

`/admin/inbox`. 자동 생성된 `inbox` 상태 자산들의 검수 대기열. 어드민(JH) 이 30분 내 50장 처리하는 것이 MVP 목표.

검수 흐름: 시각 확인 → 메타데이터 편집 (제목/설명/alt/카테고리/태그) → `publish` 로 전환 → 옵션으로 `/today` 큐레이션 별표 지정.

## 오늘의 자산 (`/today`)

JH 가 매일 별표 지정한 자산들의 공개 큐레이션 페이지. SEO/유입 진입점.

## 활동 로그 (`/log`)

공개 활동 페이지. 어떤 자산이 언제 추가됐는지 / 신고 처리 / 큐레이션 이력 등 *투명성* 목적.

## 생성 잡 (Generation Job)

자동 생성 요청 1건. 테이블: `generation_jobs`.

라이프사이클:
1. `pending` → Celery 큐 적재
2. `running` → 1차 Nanobanana 호출
3. `succeeded` → 자산 인박스 적재
4. `failed_primary` → 2차 `gpt-image-2` 자동 승격
5. `failed_secondary` → ComfyUI 큐 대기 (특수 워크플로우) 또는 영구 실패
6. `escalated` → 어드민에 알림

자동 승격 규칙 (1→2→3):
- API 5xx
- NSFW 필터 탈락
- CLIP score < 임계
- 같은 프롬프트 패턴의 신고 누적 자산

## 프롬프트 풀 (Prompt Pool)

카테고리별 프롬프트 템플릿 시드. `A4_프롬프트풀_시드_샘플.md` 가 원본. Phase 3 진행 중 항목 "프롬프트 템플릿과 결과 검수" 가 이 풀의 운영화.

## 신고 (Report)

공개 `/report` 페이지에서 사용자가 접수. GPT-5 가 1차 자동 분류 (저작권/유해/오분류/기타) → 어드민 검토 → 자산 takedown 또는 기각 + 감사 로그.

## 라이선스

- A5 문서가 한·영 본문 원본.
- 모든 발행 자산에 라이선스 메타데이터 + EXIF/HTML meta 로 *AI 생성물 명시* 의무.
- 향후 C2PA 실제 서명은 *MVP 범위 외* (Phase 후속).

## 페르소나 (B1/B2 기준)

| 페르소나 | 핵심 욕구 |
|---|---|
| 콘텐츠 제작자 | 한국어 시나리오·인물에 맞는 이미지 즉시 다운로드 |
| 마케터 | 광고 소재로 쓸 수 있는 무료/저작권 안전 자산 |
| 교육자 | 강의 슬라이드용 깨끗한 일러스트 |
| 1인 사업자 | 브랜드 이미지·SNS 용 비상업 가능 자산 |

## 비즈니스 모델 (운영 가시성용)

- MVP: **무료 + AdSense 미적용** (Phase 3 후속에서 AdSense 신청).
- 무제한 외부 API 키 보유 → *비용 캡* 보다 *호출량/장애/도용 감시* 우선.
- 장기: 영어/일본어 확장 → 메타 콘텐츠(블로그/가이드) → AdSense → 디지털 상품/B2B.

## 비즈니스 의사결정자

JH (1인 운영자, 광고/마케팅 본업).
