# 구현 시작 README

이 프로젝트 폴더를 Codex/Claude Code에 전달할 때는 아래 순서대로 읽게 한다.

## 0. 프로젝트 고정값

- 최종 프로젝트명: **Vaultix**
- GitHub 저장소: `https://github.com/naral3221-dotcom/vaultix.git`
- 코드/인프라 식별자: `vaultix`
- Python 패키지명: `vaultix_api`
- Docker prefix/network: `vaultix-`, `vaultix_internal`
- 로컬 LLM 참고 경로: `C:\AI\llm` (Ollama가 아니라 GGUF/LM Studio 계열 모델 저장소)

## 1. 가장 먼저 읽을 문서

1. `기획서/00_IMPLEMENTATION_SPEC_v0.4.md`
2. `기획서/00_확정사항_레지스트리.md`
3. `기획서/A7_LLM_라우팅_정책.md`
4. `기획서/A1_데이터모델_DDL.md`
5. `기획서/A2_API_스펙.md`
6. `기획서/B1_브랜드_디자인시스템.md`
7. `기획서/B2_정보아키텍처_와이어프레임.md`
8. `기획서/01_Phase0_기반셋업.md`
9. `기획서/02_Phase1_이미지MVP.md`

`AI컨텐츠허브_기획안_v0.3.md`, `v0.3_정합성검증_환경충돌_보고서.md`, `기획서/99_최종검토_정합성보고서.md`는 역사 문서다. 구현 기준으로 쓰지 않는다.

## 2. MVP 범위

- Phase 0 + Phase 1만 구현한다.
- 한국어 이미지 자산 사이트만 만든다.
- 이미지 생성은 Nanobanana API → OpenAI `gpt-image-2` → ComfyUI 특수 워크플로우 순서다.
- Ollama 컨테이너, Replicate, fal.ai는 폐기된 결정이다.
- `C:\AI\llm`의 Qwen3.6 GGUF 모델은 MVP 기본 라우팅에 넣지 않고 보조/실험용으로만 둔다.
- PPT/SVG/DOCX, 일본어, 영어, OAuth, AdSense, 블로그 자동화는 MVP 이후 배포로 넘긴다.

## 3. MVP 이후

MVP가 끝나면 `기획서/07_PostMVP_배포전략.md`의 Release 1부터 순서대로 진행한다.

권장 순서:

1. MVP 안정화
2. 일본어 출시
3. 레시피 공개 + ComfyUI 특수 워크플로우
4. 콘텐츠 타입 확장 1차
5. 메타 콘텐츠 + AdSense 준비
6. AdSense 신청
7. 영어/글로벌 확장

## 4. 구현 에이전트용 한 줄 지시

```text
프로젝트명은 Vaultix이고 저장소는 https://github.com/naral3221-dotcom/vaultix.git 입니다. 먼저 기획서/00_IMPLEMENTATION_SPEC_v0.4.md를 읽고, 충돌 시 그 문서를 최우선으로 삼아 Phase 0 Sprint 0부터 구현을 시작해 주세요.
```

