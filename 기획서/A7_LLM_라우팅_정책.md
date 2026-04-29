# A7 — LLM/이미지 모델 라우팅 정책

> **목적**: LLM 및 이미지 생성 모델의 사용처별 매핑·선택 기준·운영 규칙을 한 곳에 정리.
> **상태**: v0.4 확정 (D-13/D-14에 의거)
> **변경 시**: 본 문서 + `00_확정사항_레지스트리.md` 동시 갱신

---

## 0. 핵심 원칙

1. **모든 외부 모델 호출은 각사 최신 플래그십 모델로 통일** — 품질 우선, 비용은 고려하지 않음 (JH가 4개사 API 무제한 보유)
2. **Ollama 컨테이너를 운영하지 않음** — VPS CPU 자원을 보존하고 배포 복잡도를 줄임
3. **로컬 GGUF 모델은 보조/실험용** — `C:\AI\llm`에 모델은 있으나 MVP 기본 라우팅에는 넣지 않음
4. **임베딩만 로컬 sentence-transformers 사용** — 가벼움(100MB), API 비용 누적 회피
5. **이미지 생성: API 우선, ComfyUI는 보조** — 데스크탑 항시 가동 불가가 전제
6. **모델 호출은 모두 단일 라우팅 레이어 통과** (`backend/llm_router.py`) — 모델 교체·A/B·로깅 일원화

### 0.1 로컬 모델 환경 (D-21)

현재 로컬 PC에는 Ollama 저장소가 아니라 LM Studio/llama.cpp 계열 GGUF 모델 폴더가 있다.

| 항목 | 내용 |
|------|------|
| 기준 경로 | `C:\AI\llm` |
| 저장소 성격 | `lmstudio-community` 하위 GGUF 모델 저장소 |
| 확인 모델(27B) | `Qwen3.6-27B-GGUF/Qwen3.6-27B-Q6_K.gguf` + `mmproj-Qwen3.6-27B-BF16.gguf` |
| 확인 모델(35B) | `Qwen3.6-35B-A3B-GGUF/Qwen3.6-35B-A3B-Q4_K_M.gguf`, `Qwen3.6-35B-A3B-Q6_K.gguf` + `mmproj-Qwen3.6-35B-A3B-BF16.gguf` |
| 운영 판단 | MVP 서버 스택에는 포함하지 않는다. 후속 배포에서 오프라인 평가, 프롬프트 검수, 대량 초안 생성 보조 워커로 쓸 수 있다. |

> **중요**: 구현 에이전트는 `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, Ollama Docker service를 만들지 않는다. 로컬 GGUF 사용이 필요해지면 별도 결정으로 `LOCAL_LLM_BASE_URL` 같은 OpenAI-compatible endpoint를 추가한다.

---

## 1. 모델 라이브러리 (보유 API 키 기준)

| 회사 | 보유 키 | 권장 사용 모델 (2026-04-28 기준) | 강점 |
|------|:---:|--------------------------------|------|
| Anthropic | ✅ | **Claude Opus 4.6 / Sonnet 4.6** | 한국어·긴 문맥·톤 일관성 최강, 인사이트 통합·블로그 본문 |
| OpenAI | ✅ | **GPT 최신 플래그십** (예: GPT-5 / GPT-4.x 최신) + **`gpt-image-2`** | 균형 잡힌 품질, 이미지 생성 보조 |
| Google AI | ✅ | **Gemini 2.5 Pro** (또는 시점 최신 Pro/Ultra) | 멀티모달, 대용량 토픽 분석 |
| Z.AI | ✅ | **GLM 4.6** (또는 시점 최신 상위 모델) | 빠른 분류, 한국어/중국어 보조 |
| Nanobanana 서비스 | ✅ | 서비스 제공 최신 이미지 모델 | 이미지 생성 메인 |

> **운영 규칙**: 본 문서는 모델명을 명시하지만 — "각사 최신 플래그십"이 시간이 지나며 변하므로, **3개월에 1회 본 표를 검토하고 갱신**. 검토 일자는 §6 변경 이력에.

---

## 2. LLM 사용처 매트릭스 (8개 시나리오)

| # | 사용처 | Phase | 1차 모델 | 폴백 | 호출 빈도 | 비고 |
|---|--------|:---:|---------|------|:---:|------|
| 1 | 자산 메타데이터 생성 (제목·설명·alt) | 1 | **Gemini 2.5 Pro** | GPT-5 | 자산당 1회 (일 50~200회) | 대량 처리, 멀티모달(이미지→텍스트) |
| 2 | 카테고리·태그 자동 분류 | 1 | **GLM 4.6** | Gemini 2.5 Pro | 자산당 1회 | 단순 분류, 빠른 응답 우선 |
| 3 | 번역 (DeepL 보조) | 2 | **Claude Sonnet 4.6** | GPT-5 | DeepL 신뢰도 < 임계 시 | 마케팅 카피·뉘앙스 보존 |
| 4 | 블로그 초안 생성 | 3 | **Claude Opus 4.6** | GPT-5 | 주 5~10편 | 한국어 품질 + 5,000자 긴 문맥 |
| 5 | JH 인사이트 + 초안 통합 | 3 | **Claude Opus 4.6** | — | 주 5~10편 | 톤 일관성 |
| 6 | 토픽 발굴 점수화 | 3 | **Gemini 2.5 Pro** | GLM 4.6 | 주 1회 (50~100토픽) | 트렌드+검색량+경쟁 종합 평가 |
| 7 | 자산↔가이드 임베딩 매칭 | 3 | **sentence-transformers (로컬)** | — | 자산·가이드 생성 시 1회 | 384d, CPU 가벼움, API 미사용 |
| 8 | 신고/abuse 자동 분류 | 1+ | **GPT-5** | Gemini 2.5 Pro | 신고 발생 시 (일 0~5회) | 단순 분류, 균형 모델 |

---

## 3. 라우팅 레이어 설계

### 3.1 단일 진입점

```python
# backend/llm_router.py (개념 코드)

from enum import Enum

class TaskType(str, Enum):
    METADATA_GEN = "metadata_gen"
    CATEGORIZE = "categorize"
    TRANSLATE_NUANCE = "translate_nuance"
    BLOG_DRAFT = "blog_draft"
    INSIGHT_MERGE = "insight_merge"
    TOPIC_SCORE = "topic_score"
    EMBED = "embed"
    REPORT_CLASSIFY = "report_classify"

ROUTING = {
    TaskType.METADATA_GEN:    ("gemini", "gemini-2.5-pro"),
    TaskType.CATEGORIZE:      ("zai",    "glm-4.6"),
    TaskType.TRANSLATE_NUANCE:("anthropic","claude-sonnet-4-6"),
    TaskType.BLOG_DRAFT:      ("anthropic","claude-opus-4-6"),
    TaskType.INSIGHT_MERGE:   ("anthropic","claude-opus-4-6"),
    TaskType.TOPIC_SCORE:     ("gemini", "gemini-2.5-pro"),
    TaskType.EMBED:           ("local",  "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
    TaskType.REPORT_CLASSIFY: ("openai", "gpt-5"),
}

FALLBACK = {
    "gemini-2.5-pro":   ("openai", "gpt-5"),
    "glm-4.6":          ("gemini", "gemini-2.5-pro"),
    "claude-opus-4-6":  ("openai", "gpt-5"),
    "claude-sonnet-4-6":("openai", "gpt-5"),
    "gpt-5":            ("gemini", "gemini-2.5-pro"),
}

async def call(task: TaskType, prompt: str, **kwargs):
    provider, model = ROUTING[task]
    try:
        return await dispatch(provider, model, prompt, **kwargs)
    except (RateLimit, ProviderDown, Timeout) as e:
        log_failover(model, e)
        fb_provider, fb_model = FALLBACK[model]
        return await dispatch(fb_provider, fb_model, prompt, **kwargs)
```

### 3.2 로깅 (필수)

모든 호출은 `llm_call_log` 테이블에 기록:

```sql
CREATE TABLE llm_call_log (
    id BIGSERIAL PRIMARY KEY,
    task_type VARCHAR(50) NOT NULL,
    provider VARCHAR(20) NOT NULL,
    model VARCHAR(80) NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    latency_ms INTEGER,
    cost_estimate_usd NUMERIC(10,6),
    success BOOLEAN NOT NULL,
    error_kind VARCHAR(50),
    failover_from VARCHAR(80),
    request_id VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ON llm_call_log (task_type, created_at DESC);
CREATE INDEX ON llm_call_log (model, created_at DESC) WHERE success = false;
```

→ 어드민 대시보드(T-12)에 "오늘 LLM 호출 N회 / 실패율 X% / 평균 지연 Y ms" 위젯 노출.

### 3.3 Rate Limit 대응

각사 분당 호출 한도가 다름. 라우터에서 token bucket으로 글로벌 컨트롤:
- Anthropic: 분당 1,000 RPM (Tier에 따라 다름) → 보수적으로 600 RPM 설정
- OpenAI: 분당 10,000 TPM (Tier 4+) → 토큰 기준 제한
- Gemini: 분당 360 RPM (Pro) → 보수적 200 RPM
- Z.AI: 분당 60 RPM → 60 그대로

초과 시 Celery 큐에서 자동 백오프 + 폴백 모델로 전환.

---

## 4. 이미지 생성 라우팅 (D-1 변경 반영)

### 4.1 새 라인업

| 순위 | 제공자 | 용도 | 비고 |
|:---:|--------|------|------|
| 1차 (메인) | **Nanobanana API** | 일반 이미지 대량 생성 | 빠르고 저렴, 무제한 |
| 2차 (품질) | **OpenAI `gpt-image-2`** | Nanobanana 품질 부족·실패 시 자동 승격 | OpenAI API 키로 호출 |
| 3차 (특수) | **데스크탑 ComfyUI** | ControlNet/LoRA/캐릭터 일관성 등 API 미지원 워크플로우 | 가용 시간대만 (평일 22~08, 주말) |

### 4.2 자동 승격 규칙

이미지 생성 결과가 다음 조건 중 하나면 → 다음 순위 자동 재시도:
- API 응답 5xx
- 생성 이미지가 NSFW 필터 탈락
- 이미지 미적 점수(CLIP score) < 임계
- 사용자 신고 누적 자산의 같은 프롬프트 패턴

### 4.3 ComfyUI 특수 워크플로우 정의

ComfyUI는 메인 라인이 아니지만 **차별화 워크플로우 전용**으로 가치를 가짐. 예시:

| 워크플로우 | 용도 | 활용 |
|------------|------|------|
| `consistent_character.json` | 같은 캐릭터 12장 시리즈 | PPT 시리즈 자산, 만화 컷 |
| `controlnet_pose.json` | 특정 포즈 강제 | 비즈니스 포즈 일관성 |
| `style_lora.json` | 한국 일러스트 스타일 LoRA | K-콘텐츠 차별화 |
| `inpaint_iterative.json` | 부분 수정 반복 | 큐레이션 후 자산 보정 |

→ 이 워크플로우들은 데스크탑 가용 시간대에만 큐잉. 인박스에서 승격 가능 ("이 자산은 시리즈로 만들고 싶다" 토글).

---

## 5. 운영 규칙

### 5.1 모델 변경 절차

1. 새 플래그십 모델 출시 인지 → A7 §1 표 갱신 후보 추가
2. **카나리 호출**: 라우터에 `experimental` 플래그 추가, 호출의 5%만 신모델로 라우팅 (1주)
3. 품질 비교: 같은 프롬프트로 옛/새 모델 응답 100건 비교 → JH 평가
4. OK이면 메인 모델 교체, 옛 모델은 폴백으로 강등
5. 변경 이력 §6에 기록

### 5.2 장애 알림

- 단일 모델 5분 내 실패율 > 20% → Telegram P2 알림
- 폴백 체인 전체 실패(예: Anthropic + OpenAI 동시 다운) → P0 알림 + `/admin/panic` 자동 발동 검토
- 일 누적 호출 < 평균 50% → P1 (잠재적 큐 정체)

### 5.3 비용 모니터링 (참고용)

JH 무제한 키 보유라 비용 천장은 없지만, **호출량 추적은 운영 가시성 차원에서 필수**:
- 월별 모델별 토큰 합계 → 어드민 대시보드 노출
- 비정상 폭증 (예: 평소 대비 5배) → P1 알림
- 호출 비용 추정치 (해당 시점 공식 단가 기준)는 참고용으로 기록

---

## 6. 변경 이력

| 일자 | 변경 | 영향 |
|------|------|------|
| 2026-04-27 | 최초 작성 (D-13 LLM 정책 변경, D-14 이미지 라인 변경 반영) | T-01 보강, A3 워커 설계 갱신 필요 |

---

## 부록 — 폐기된 결정과 이유

| 폐기 대상 | 이유 | 대체 |
|----------|------|------|
| Ollama Qwen 2.5 7B/14B (VPS CPU) | 4개사 API 무제한 키 보유로 자체 호스팅 불필요 + VPS CPU 보존. 현재 로컬 모델은 Ollama가 아니라 `C:\AI\llm`의 GGUF 저장소 | 외부 API 라우팅 (§2), 로컬 GGUF는 D-21 보조/실험용 |
| Replicate API 폴백 | Nanobanana + `gpt-image-2`가 더 나은 1·2차 라인 | 라인업에서 제외 |
| ComfyUI를 1차 메인으로 운영 | 데스크탑 항시 가동 불가 (JH 환경) | ComfyUI는 특수 워크플로우 전용 (§4.3) |
| Claude Haiku API 월 $5 한도 | 비용 우려 무의미 (무제한 키), 더 좋은 모델 사용 가능 | Claude Sonnet/Opus 4.6 전면 사용 |

