# 00 — v0.4 구현 기준 단일본

> **목적**: Codex/Claude Code 같은 구현 에이전트에게 전달할 최상위 실행 문서.
> **상태**: v0.4 기준. 구현 시 이 문서를 먼저 읽고, 충돌 시 본 문서를 우선한다.
> **작성일**: 2026-04-29

---

## 0. 프로젝트 고정값

| 항목 | 값 |
|------|------|
| 최종 프로젝트명 | **Vaultix** |
| 코드/인프라 식별자 | `vaultix` |
| GitHub 저장소 | `https://github.com/naral3221-dotcom/vaultix.git` |
| Python 패키지명 | `vaultix_api` |
| Docker Compose project | `vaultix` |
| 컨테이너 prefix | `vaultix-` |
| Docker 네트워크 | `vaultix_internal` |
| 호스트 데이터 경로 | `/var/lib/vaultix/...` |

---

## 1. 문서 우선순위

구현 중 문서끼리 충돌하면 아래 순서로 판단한다.

1. `00_IMPLEMENTATION_SPEC_v0.4.md` — 지금 읽는 문서
2. `00_확정사항_레지스트리.md` — B/T/D 결정 원장
3. `A7_LLM_라우팅_정책.md` — LLM/이미지 모델 최신 기준
4. `A1_데이터모델_DDL.md`, `A2_API_스펙.md`
5. `B1_브랜드_디자인시스템.md`, `B2_정보아키텍처_와이어프레임.md`
6. `01_Phase0_기반셋업.md`, `02_Phase1_이미지MVP.md`
7. `99B_보강안_v0.4_제안.md` — 결정 배경 참고
8. `AI컨텐츠허브_기획안_v0.3.md`, `99_최종검토_정합성보고서.md` — 역사 문서. 구현 기준으로 사용하지 않는다.

---

## 2. MVP 구현 범위

MVP는 **Phase 0 + Phase 1**만 구현한다.

### 2.1 반드시 구현

- 모노레포: `apps/api`, `apps/web`, `infra`
- FastAPI + PostgreSQL 17 + Redis + Celery
- Next.js App Router + TypeScript + Tailwind + shadcn/ui
- Auth.js v5 기반 회원가입/로그인/이메일 인증
- 이미지 자산 탐색, 상세, 다운로드
- 관리자 큐레이션 인박스
- 이미지 자동 생성 파이프라인
  - 1차: Nanobanana API
  - 2차: OpenAI `gpt-image-2`
  - 3차: ComfyUI 특수 워크플로우용 예약만. Phase 1 일반 생성에는 사용하지 않는다.
- LLM 라우팅 레이어
  - Ollama 컨테이너는 사용하지 않는다.
  - `C:\AI\llm`의 로컬 GGUF 모델은 MVP 기본 라우팅에 넣지 않고 보조/실험용으로 둔다.
  - 메타데이터/분류/신고 분류는 A7 기준 외부 API 라우터를 통과한다.
- `llm_call_log`, `cost_meter`, `asset_metrics_daily` 기반 운영 가시성
- `/admin/panic`
- `/report` 신고 접수
- `/today`, `/log` 공개 페이지의 골격
- Listmonk 뉴스레터 셋업과 `/newsletter`
- EXIF/HTML meta 기반 AI 생성물 명시
- 라이선스, 개인정보처리방침, About, Contact
- pgBackRest 또는 wal-g 기반 WAL 백업, RPO 1h/RTO 4h 목표
- 자산 SHA-256 체크섬 생성

### 2.2 MVP에서는 하지 않음

- 영어/일본어 공개 출시
- PPT/SVG/DOCX/XLSX/HTML 템플릿 생성
- OAuth Google/Kakao
- 즐겨찾기/컬렉션
- AdSense 신청
- 블로그 30편 자동화 파이프라인
- C2PA 실제 서명
- B2B/API/유료 상품
- 사용자 노출형 실시간 생성 서비스

위 항목은 DB/API 확장 여지는 남기되, MVP 구현 목표에 넣지 않는다.

---

## 3. 최신 확정 결정

| 영역 | 최종 결정 |
|------|----------|
| 프로젝트명 | Vaultix. 저장소는 `https://github.com/naral3221-dotcom/vaultix.git` |
| LLM | Ollama 컨테이너 폐기. Anthropic/OpenAI/Google AI/Z.AI 외부 API 라우팅 |
| 이미지 | Nanobanana API → `gpt-image-2` → ComfyUI 특수 워크플로우 |
| 로컬 모델 | `C:\AI\llm`의 Qwen3.6 GGUF 모델은 LM Studio/llama.cpp 계열 보조 자원. MVP 필수 아님 |
| 임베딩 | sentence-transformers 로컬 사용. LLM 자체 호스팅과 별개 |
| DB | PostgreSQL 17 |
| 다국어 | MVP는 한국어만. 다음 배포에서 일본어 우선, 영어는 이후 |
| 비용 | 무제한 키 보유 전제. 비용 캡보다 호출량/장애/도용 감시를 우선 |
| 운영 | `/admin/panic`, 백업 리허설, 신고 처리, 품질 대시보드를 MVP 안전망으로 포함 |

---

## 4. 구현 순서

### 4.1 Sprint 0 — 기준선 정리

- 저장소 생성, 모노레포 골격 작성
- 원격 저장소는 `https://github.com/naral3221-dotcom/vaultix.git` 사용
- `.env.example` 작성
- Docker Compose 최소 스택: postgres, redis, api, web, celery, celery-beat, plausible, uptime-kuma, listmonk
- Ollama/Replicate/fal.ai 관련 설정은 넣지 않는다. 로컬 GGUF 모델 연동은 MVP 이후 별도 결정 전까지 보류한다.
- OpenAI 이미지 모델 환경변수는 `OPENAI_IMAGE_MODEL=gpt-image-2`로 둔다.

### 4.2 Sprint 1 — 인프라와 배포

- 시스템 nginx server block 추가
- Tailscale 전용 admin 노출
- GitHub Actions CI/CD
- Sentry, Uptime Kuma, Plausible
- pgBackRest 또는 wal-g 백업 PoC
- `/healthz`와 배포 헬스체크

### 4.3 Sprint 2 — 인증과 기본 자산

- Auth.js v5 DB 세션 검증
- FastAPI 세션 미들웨어
- users/sessions/email_verifications/password_resets
- categories/tags/assets/asset_files
- 홈, 탐색, 자산 상세의 읽기 흐름

### 4.4 Sprint 3 — 다운로드와 보안

- signed URL + Redis nonce
- 시간당 30회 rate limit
- 이메일 인증 전 다운로드 제한
- Turnstile
- X-Accel-Redirect
- 다운로드 완료 기준 카운트

### 4.5 Sprint 4 — 생성 파이프라인

- `generation_jobs`
- Nanobanana adapter
- OpenAI `gpt-image-2` adapter
- 이미지 검증, 점수화, 썸네일/WebP 생성
- LLM 라우터 기반 title/description/alt/tag 생성
- `llm_call_log`와 provider 실패율 추적

### 4.6 Sprint 5 — 운영자 도구

- `/admin/inbox`
- `/admin/dashboard` v0/v1
- `/admin/panic`
- `/admin/takedowns`
- `/admin/log/{date}`
- 인박스에서 `/today` 큐레이션 별표 지정

### 4.7 Sprint 6 — 공개 신뢰 페이지와 베타

- `/license`, `/privacy`, `/about`, `/contact`, `/report`, `/newsletter`, `/today`, `/log`
- EXIF/HTML meta AI 생성 명시
- robots/sitemap/image-sitemap
- ImageObject JSON-LD
- 베타 5명 시나리오 검증

---

## 5. MVP 완료 조건

- 베타 사용자 5명이 가입 → 이메일 인증 → 탐색 → 다운로드 완료
- 일 자동 생성 50장 이상, 7일 연속
- Nanobanana 생성 비중 80% 이상, `gpt-image-2` 폴백 20% 이하
- ComfyUI 일반 생성 비중 0%. 특수 워크플로우는 다음 배포부터
- 큐레이션 인박스에서 30분 내 50장 처리 가능
- `/admin/panic` on/off 검증 완료
- `/report` 신고 1건 시뮬레이션 처리 완료
- pgBackRest/wal-g 백업과 복구 리허설 완료
- Sentry 에러율 0.5% 미만
- Uptime Kuma 7일 99% 이상
- 라이선스/Privacy/About/Contact 발행
- 자산 체크섬 검증 cron 손상 0건

---

## 6. 구현 에이전트에게 줄 지시

아래 지시를 Codex/Claude Code 작업 시작 프롬프트 앞부분에 붙인다.

```text
이 프로젝트는 v0.4 구현 기준으로 진행한다.
최종 프로젝트명은 Vaultix이며, GitHub 저장소는 https://github.com/naral3221-dotcom/vaultix.git 이다.
가장 먼저 기획서/00_IMPLEMENTATION_SPEC_v0.4.md를 읽고, 문서 충돌 시 그 문서를 우선한다.
AI컨텐츠허브_기획안_v0.3.md와 99_최종검토_정합성보고서.md는 역사 문서이므로 구현 기준으로 삼지 않는다.
Ollama 컨테이너, Replicate, fal.ai는 폐기된 결정이다. C:\AI\llm의 로컬 GGUF 모델은 MVP 기본 라우팅에 넣지 않는다.
이미지 생성은 Nanobanana API → OpenAI gpt-image-2 → ComfyUI 특수 워크플로우 순서다.
MVP에서는 한국어 이미지 자산 사이트만 만든다.
PPT/SVG/DOCX, 다국어, OAuth, AdSense, 블로그 자동화는 다음 배포로 넘긴다.
작업은 Sprint 0부터 순서대로 진행하고, 각 Sprint마다 테스트와 체크리스트를 업데이트한다.
```

---

## 7. MVP 이후 연결

MVP 완료 후에는 [07_PostMVP_배포전략.md](./07_PostMVP_배포전략.md)를 따라 작은 배포 단위로 이어간다.

원칙:
- 큰 Phase를 한 번에 열지 않는다.
- 매 배포는 사용자 가치 1개 + 운영 안정성 1개 이하로 제한한다.
- 매 배포마다 Search Console/Plausible/Sentry/Uptime Kuma 결과를 보고 다음 우선순위를 조정한다.

