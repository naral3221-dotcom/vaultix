---
project_name: Vaultix
project_type: monorepo
primary_languages: [Python, TypeScript]
tech_stack: [FastAPI, Next.js, PostgreSQL, Redis, Celery, Docker Compose, Tailwind, shadcn/ui, Auth.js v5, Alembic, SQLAlchemy]
domain: AI 생산성 에셋 허브 — 한국어 이미지 자산 카탈로그 및 자동 생성 파이프라인
schema_version: "1.0"
last_updated: 2026-05-14T04:24:07+09:00
---

# Vaultix — LLM Wiki Index

> AI 생산성 에셋 허브. 한국어 이미지 자산 큐레이션·자동 생성·다운로드. 1인 운영(JH, 본업 광고/마케팅) + main-hub VPS + 데스크탑 ComfyUI 하이브리드 구성.

## 페이지 목록

| 페이지 | 한 줄 요약 | 마지막 갱신 |
|---|---|---|
| [overview](overview.md) | 프로젝트가 뭐고 왜 존재하는지 + 최근 변경 | 2026-05-14 |
| [architecture](architecture.md) | 모노레포 구조 + 데이터/이미지/LLM 흐름 + 디렉토리 트리 | 2026-05-14 |
| [domain](domain.md) | 비즈니스 도메인 용어 (자산·인박스·생성잡 등) | 2026-05-14 |
| [modules](modules.md) | apps/api, apps/web, infra 모듈 책임 분담 | 2026-05-14 |
| [dependencies](dependencies.md) | 외부 의존성 (Nanobanana, OpenAI, Anthropic, Gemini, Z.AI, Resend, Turnstile, ComfyUI) | 2026-05-14 |
| [decisions](decisions.md) | 영속 결정 레지스트리 (D-1~D-21 + 후속) | 2026-05-14 |
| [conventions](conventions.md) | 코딩·네이밍·테스트·배포 컨벤션 | 2026-05-14 |
| [glossary](glossary.md) | 기술 약어와 내부 용어 | 2026-05-14 |

## 외부 참조 (위키 영역 밖)

- 사용자 컨벤션: [`../../CLAUDE.md`](../../CLAUDE.md) — *없음 (인간 작성 룰 부재. 글로벌 룰은 `/home/openclaw/claude-forge/rules/` 사용)*
- 구현 기준 단일본: [`../../기획서/00_IMPLEMENTATION_SPEC_v0.4.md`](../../기획서/00_IMPLEMENTATION_SPEC_v0.4.md)
- 결정 레지스트리 원본: [`../../기획서/00_확정사항_레지스트리.md`](../../기획서/00_확정사항_레지스트리.md)
- LLM 라우팅: [`../../기획서/A7_LLM_라우팅_정책.md`](../../기획서/A7_LLM_라우팅_정책.md)
- 데이터 모델: [`../../기획서/A1_데이터모델_DDL.md`](../../기획서/A1_데이터모델_DDL.md)
- API 스펙: [`../../기획서/A2_API_스펙.md`](../../기획서/A2_API_스펙.md)
- 브랜드/디자인: [`../../기획서/B1_브랜드_디자인시스템.md`](../../기획서/B1_브랜드_디자인시스템.md), [`B2_정보아키텍처_와이어프레임.md`](../../기획서/B2_정보아키텍처_와이어프레임.md)
- 로드맵: [`../../docs/ROADMAP.md`](../../docs/ROADMAP.md)

## 위키 사용 원칙

- **수정 시**: 해당 페이지의 `last_updated` frontmatter 도 함께 갱신.
- **결정 승격**: `state.md` 의 "중요 결정" 이 영속성 증명되면 `decisions.md` 로 옮기고 `state.md` 에서 제거 (중복 방지).
- **반복 함정 발견**: `log.md` 의 `gotcha` 3+ 회 누적 시 `gotchas.md` 신규 생성 후 통합.
- **모순 발견**: `lint` 사이클에서 자동 검출. 즉시 사용자에게 한 줄 보고.
