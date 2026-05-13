# Project State — Vaultix

> 마지막 업데이트: 2026-05-14T04:24:07+09:00
> 마지막 압축: 없음

## 현재 작업

- **Phase**: Phase 3 (Active, 85%) — 이미지 공급 파이프라인
- **수정 중 파일**: 없음 (초기화 시점)
- **사용자 마지막 지시 (원문)**: "/agent-init"

## 중요 결정 (되돌리기 어렵거나 영향 큼)

- [2026-05-14] `.agent/` 메모리 인프라 초기화 (`/agent-init` 수동 실행). 이후 `state.md` / `log.md` / `wiki/` 가 모든 후속 작업의 단일 진실 공급원.

## 미해결 질문·블로커

- 프로덕션 `OPENAI_API_KEY` 설정과 생성 자산 저장 확인 (ROADMAP.md "Next Major Milestone")

## 잊으면 안 되는 제약·불변량

- **MVP 범위**: Phase 0 + Phase 1 만. 한국어 이미지 자산 사이트 한정.
- **이미지 생성 라인업 (고정)**: Nanobanana API → OpenAI `gpt-image-2` → ComfyUI 특수 워크플로우. Replicate / fal.ai / Ollama 컨테이너는 *폐기된 결정*.
- **LLM 호출은 모두 OpenClaw Gateway 경유** (글로벌 룰 — 직접 SDK 임포트 금지). MVP 라우팅 스펙은 `A7_LLM_라우팅_정책.md` 기준이되, 실제 호출은 OpenClaw 경유로 통제.
- **로컬 GGUF 모델** (`C:\AI\llm` 의 Qwen3.6 등) 은 MVP 기본 라우팅에 *포함하지 않음*. 보조/실험용.
- **문서 우선순위 (충돌 시)**: `기획서/00_IMPLEMENTATION_SPEC_v0.4.md` → `00_확정사항_레지스트리.md` → `A7_LLM_라우팅_정책.md` → A1/A2 → B1/B2 → Phase 0/1 문서. `AI컨텐츠허브_기획안_v0.3.md` 와 `99_최종검토_정합성보고서.md` 는 *역사 문서* — 구현 기준으로 사용 금지.
- **호스트 데이터 경로**: `/var/lib/vaultix/...`. Docker 식별자 prefix `vaultix-`, network `vaultix_internal`.
- **DB**: PostgreSQL 17 (다른 버전 가정 금지).
- **포트 (개발)**: Web 8301, API 8302, Postgres 5440, Redis 6380.
