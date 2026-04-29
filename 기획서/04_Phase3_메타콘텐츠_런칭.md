# Phase 3 — 메타 콘텐츠 자동화 + 공개 런칭 상세 기획서

> **목적**: AI 컨텐츠 사이트의 정체성을 완성하는 **메타 콘텐츠(블로그·가이드)** 자동화 파이프라인을 가동하고, AdSense 신청·승인·트래픽 확보·뉴스레터·소셜 자동 발행을 통해 손익분기 진입 단계로 들어간다.
> **선행**: Phase 2 §7 진입 조건 모두 통과 / DeepL 누적 사용량·예산 확인
> **작성일**: 2026-04-27

---

## 1. 목표 & 완료 조건

### 1.1 목표

1. **메타 콘텐츠 6단계 파이프라인 가동**: 토픽 발굴 → 큐레이션 → 초안 → 인사이트 → 통합 → 발행
2. **블로그 30편+ 사전 발행** 후 AdSense 신청
3. **AdSense 승인 + 첫 광고 수익**
4. **주간 뉴스레터 발송 자동화**
5. **Pinterest 자동 발행**으로 외부 트래픽 채널 확보
6. **프롬프트 라이브러리 + AI 도구 디렉토리** 발행 (제휴 마케팅 시작)

### 1.2 완료 조건 (체크리스트)

**메타 콘텐츠 파이프라인**
- [ ] 토픽 발굴 자동화 (Google Trends + RSS + 검색 로그) 주 1회 실행
- [ ] Telegram/Slack 봇이 매주 월요일 토픽 후보 20개 푸시
- [ ] 큐레이션 인박스에서 토픽 5분 처리 (승인/폐기)
- [ ] 승인된 토픽 → 자동 초안 작성 (A7 LLM 라우터, 기본 Claude Opus/Sonnet급)
- [ ] JH 인사이트 추가 (음성 메모 → Whisper → 텍스트, 또는 직접 메모)
- [ ] 통합 + 다듬기 (LLM)
- [ ] 최종 검수 + 발행 → 다국어 자동 번역 발행

**블로그 페이지**
- [ ] /blog 인덱스 + /blog/[slug] 상세 + 카테고리·태그 페이지 (한·일, 영어는 Phase 4 이후)
- [ ] 사전 발행 30편 (도구 리뷰 10 / 가이드 10 / 워크플로우 5 / 사례연구 5)
- [ ] 본문에 자산 인라인 카드 (CTA 역할)

**프롬프트 라이브러리·도구 디렉토리**
- [ ] /prompts 페이지 + 50개 프롬프트 (use case별 분류, 복사 카운트)
- [ ] /tools 페이지 + 30개 AI 도구 + JH 평점·리뷰 (제휴 링크 5개 이상)

**AdSense + 광고**
- [ ] AdSense 신청 → 승인
- [ ] B1 §13.1 모든 광고 자리 활성화
- [ ] 광고 디자인 가이드 (좌측 amber 라인 + "광고" 라벨) 적용
- [ ] 첫 달 광고 수익 데이터 확보

**소셜·뉴스레터**
- [ ] Pinterest 비즈니스 계정 + 자동 발행 (자산 핀)
- [ ] 쿠팡 파트너스 가입 + 블로그 자연스러운 제휴 링크 5개+
- [ ] 주간 뉴스레터 자동 발송 (Listmonk + 자동 컨텐츠)

**KPI**
- [ ] 월 PV 5,000+
- [ ] 가입 사용자 200+
- [ ] 뉴스레터 구독자 100+

---

## 2. 작업 분해 (WBS)

> W1~W10은 묶음 단위 + 의존성 순서일 뿐 일정 약속이 아닙니다 (D-9).

### W1 — 토픽 발굴 자동화

- [ ] **1.1** Alembic 0008 마이그레이션: `topics`, `topic_sources` 추가 (A1 §10.1)
- [ ] **1.2** Google Trends 어댑터: pytrends 라이브러리, 카테고리 키워드 일 1회
- [ ] **1.3** RSS 모니터 어댑터: feedparser, 경쟁/참고 사이트 5~10개 등록
- [ ] **1.4** 자체 검색 로그 분석: PG 쿼리로 검색량 + 결과 0건 검색어 집계
- [ ] **1.5** LLM 점수화 태스크: 후보 토픽을 LLM에 보내 1) 검색 잠재력 2) JH 본업 연관성 3) AdSense 친화도 4) 기존 콘텐츠 중복도 4개 차원 점수
- [ ] **1.6** Telegram 봇: 매주 월 09:00 KST 후보 20개 푸시 (텍스트 + 점수 + "✅/❌ 버튼")
- [ ] **1.7** /admin/topics 페이지: 5분에 처리 가능한 카드형 UI

### W2 — 메타 콘텐츠 초안 생성

- [ ] **2.1** Alembic 0008 추가: `blog_posts`, `blog_post_translations`
- [ ] **2.2** 초안 생성 태스크: A7 LLM 라우터의 `BLOG_DRAFT` 사용 (블로그는 외부 API 허용 — T-01/D-13)
  - 입력: 토픽 + 카테고리 + 참고자료(자동 검색)
  - 출력: 마크다운 초안 (1500~2000자 + H2/H3 구조 + 인용 메모)
- [ ] **2.3** 자료 수집 헬퍼: SerpAPI 또는 단순 Google 검색 결과 상위 5개 URL → 본문 발췌 (Phase 3 W2~3 시점에 결정)
- [ ] **2.4** 초안 저장 → /admin/blog/posts에 status='draft' 표시
- [ ] **2.5** 초안 품질 검증: 최소 글자수 / 헤딩 구조 / 외부 링크 ≥ 3개
- [ ] **2.6** 비용 캡: Claude API 월 $30 한도

### W3 — 인사이트 추가 + 통합 + 검수 흐름

- [ ] **3.1** /admin/blog/posts/[id]/edit 페이지 (좌: 초안 / 우: 인사이트 입력 영역)
- [ ] **3.2** 음성 메모 업로드 → Whisper(로컬 또는 OpenAI Whisper API) → 텍스트 변환 자동
- [ ] **3.3** 통합 태스크: 초안 + 인사이트 → LLM에 통합 요청 → final_content 생성
- [ ] **3.4** 톤 조정 시스템 프롬프트 (B1 §3.1 친근한 프로 어조)
- [ ] **3.5** 마크다운 에디터 + 미리보기 (`@uiw/react-md-editor` 또는 자체)
- [ ] **3.6** 발행 버튼 → status='published' + 자동 다국어 번역 큐잉

### W4 — 블로그 페이지 + 다국어

- [ ] **4.1** /blog 인덱스 (B2 §4.5 와이어 1:1)
- [ ] **4.2** /blog/[slug] 상세 페이지: 마크다운 → HTML 렌더 (gray-matter + remark + rehype + Shiki)
- [ ] **4.3** 카테고리·태그 페이지
- [ ] **4.4** 본문 안 자산 인라인 카드 컴포넌트 — `[[asset:1234]]` 같은 마크업 → AssetCard 렌더
- [ ] **4.5** 작가 박스 (Phase 3은 JH 단독)
- [ ] **4.6** 다국어 번역 자동 발행 (DeepL 본문 길이 한도 1500자/회 — 분할 처리)
- [ ] **4.7** 블로그 RSS 피드 (`/blog/rss.xml`)

### W5 — 사전 콘텐츠 30편 작성 ⭐ 가장 작업량 큰 항목

- [ ] **5.1** 도구 리뷰 10편: Genspark, Flux, Midjourney, ChatGPT, Claude, Notion AI, Gamma, Canva AI, Genmo, Krea
- [ ] **5.2** 활용 가이드 10편: AI로 PPT 자동 생성 / 이력서 작성 / 인포그래픽 / SNS 카드 / 블로그 헤더 / 프롬프트 잘 쓰는 법 / 무료 자산 사이트 비교 / AI 라이선스 이해 / 한국어 AI 도구 / 본업 활용 사례
- [ ] **5.3** 워크플로우 5편: 광고 소재 / 보고서 / 발표자료 / SNS 콘텐츠 / 이력서·자소서
- [ ] **5.4** 사례 연구 5편: 본업 클라이언트 데이터 익명화 (밸런스랩 등)

> 위 30편은 본 파이프라인을 **워밍업**하는 동시에 AdSense 신청용 자산. 자동화 파이프라인 자체로 Phase 3 W6~W10에 점진 발행하면 됨.

### W6 — 프롬프트 라이브러리 + AI 도구 디렉토리

- [ ] **6.1** Alembic 0010, 0011: `prompt_library_items`, `tools`, `tool_categories`
- [ ] **6.2** /prompts 페이지 (use case 필터, 복사 버튼, 결과 예시 자산)
- [ ] **6.3** /tools 페이지 (카테고리 필터, JH 평점, 제휴 URL)
- [ ] **6.4** 50개 프롬프트 시드 입력 (use case: logo, illustration, photo, infographic 등)
- [ ] **6.5** 30개 도구 시드 입력 + 본인 사용 후기 (각 1~2문단)
- [ ] **6.6** 5개 이상 제휴 링크 등록 (쿠팡 파트너스 + AI 도구 affiliate)

### W7 — AdSense + 광고 슬롯

- [ ] **7.1** AdSense 신청 (도메인 등록 후 3개월+ 경과 확인 — Phase 2 도메인 등록부터 카운트)
- [ ] **7.2** 광고 슬롯 컴포넌트 (`<AdSlot id="..." />`) 5종 (B1 §13.1)
- [ ] **7.3** B1 §13.3 광고 디자인 룰 적용 (좌측 amber 라인 + 라벨)
- [ ] **7.4** 광고 미로드 시 영역 collapsed (CLS 방지)
- [ ] **7.5** AdSense 승인 후 광고 코드 게시
- [ ] **7.6** ads.txt 파일 생성·노출

### W8 — Pinterest 자동 발행

- [ ] **8.1** Pinterest 비즈니스 계정 생성 + 도메인 verify
- [ ] **8.2** Pinterest API v5 어댑터: 자산 → 핀 자동 생성
- [ ] **8.3** 자동 발행 정책: 신규 발행 자산 중 점수 0.7+ 만 핀 (일 5~10개)
- [ ] **8.4** 핀 description: title + 한 줄 카피 + URL
- [ ] **8.5** 보드 매핑: 카테고리 → Pinterest 보드 (비즈니스/일러스트/PPT 등)

### W9 — 주간 뉴스레터 자동화

- [ ] **9.1** 자동 컨텐츠 빌더: 매주 일요일 18:00 KST에 다음 요소 수집
  - 이번 주 인기 자산 톱 5
  - 신규 카테고리·컬렉션
  - 새 블로그 글 1~2편 요약
- [ ] **9.2** Listmonk 캠페인 자동 생성 (HTML 템플릿)
- [ ] **9.3** 월 09:00 KST 자동 발송
- [ ] **9.4** 오픈율·CTR 추적 (Listmonk 자체 + UTM)
- [ ] **9.5** 첫 5회는 수동 검수 후 발송

### W10 — 안정화 + 회고

- [ ] **10.1** Sentry/Plausible 한 달 데이터 점검
- [ ] **10.2** AdSense 승인 대기 중이면 사유별 보강
- [ ] **10.3** 베타 확장: 50명 초대 (지인·SNS·LinkedIn)
- [ ] **10.4** Phase 4 진입 전 회고
- [ ] **10.5** 비용 점검 (DeepL/Resend/Claude API 월 합계)

---

## 3. 기술 결정사항

### 3.1 결정 1 — 블로그 초안 LLM

**선택**: **A7 LLM 라우터** (사용자 노출 X, 백엔드 한정 = T-01 위배 X)

| 옵션 | 장점 | 단점 |
|------|------|------|
| A7 LLM 라우터 ⭐ | Claude Opus/Sonnet급 품질 + OpenAI/Gemini 폴백 + 호출 로그 | 외부 API 의존 |
| 단일 provider API | 구현 단순 | 장애·품질 비교·모델 교체가 어려움 |
| 로컬 Qwen 계열 | 외부 의존 낮음 | D-13으로 폐기 |

근거: 블로그는 글 자체가 콘텐츠 자산. 품질이 우선이며, D-13/D-15에 따라 자체 호스팅 LLM은 운영하지 않는다.

### 3.2 결정 2 — Whisper 위치

**선택**: **Phase 3 W3에 결정** (사용량 측정 후)

- 옵션 A: 로컬 whisper.cpp (CPU 가능, 5분 음성 30초 처리)
- 옵션 B: OpenAI Whisper API ($0.006/분, 5분 음성 = $0.03)
- 사용 빈도가 주 2~3회 → 옵션 A 추천하지만 Phase 3 W3에 실제 셋업 후 결정

### 3.3 결정 3 — 검색 자료 수집

**선택**: **SerpAPI Free + 자체 스크래핑**

- SerpAPI Free 100/월 → 부족하면 Pro
- 스크래핑은 robots.txt 준수, User-Agent 명시
- 인용은 출처 링크 + 자체 표현으로 재작성 (저작권)

### 3.4 결정 4 — Pinterest API 비용

**선택**: **무료 티어** (일 1,000 호출, 자동 발행에 충분)

### 3.5 결정 5 — 마크다운 → HTML 렌더

**선택**: **remark + rehype + Shiki (코드 하이라이트)**

- 빌드 시 정적 렌더 (Next.js Server Component)
- 인라인 자산 카드는 remark 커스텀 플러그인 (`[[asset:1234]]` → JSX)

### 3.6 결정 6 — AdSense vs Ezoic

**선택**: **AdSense 1차, 거절 시 Ezoic 2차**

- AdSense 거절 사유 흔한 것: low-value content, navigation, ads.txt 없음
- 30편 메타 콘텐츠 + 다국어 + 라이선스 명시 = 거절 사유 거의 제거
- 거절되면 사유에 따라 보강 → 재신청 (90일 후 가능)

---

## 4. 코드/설정 골격

### 4.1 토픽 발굴 (Celery beat)

```python
# apps/api/src/vaultix_api/workers/tasks_topics.py
from celery.schedules import crontab
from vaultix_api.workers.celery_app import celery_app

celery_app.conf.beat_schedule.update({
    "discover-topics-weekly": {
        "task": "vaultix.topics.discover",
        "schedule": crontab(day_of_week="mon", hour=9, minute=0),
    },
})


@celery_app.task(name="vaultix.topics.discover")
def discover_topics():
    from vaultix_api.adapters.trends import google_trends_kr
    from vaultix_api.adapters.rss import scrape_rss_sources
    from vaultix_api.services.topic_score import llm_score_topics
    from vaultix_api.adapters.telegram import push_to_jh
    from vaultix_api.db.session import SessionLocal
    from vaultix_api.models.topic import Topic

    raw = []
    raw += google_trends_kr(category_keywords=["AI", "디자인", "PPT", "이력서"])
    raw += scrape_rss_sources(feeds=[
        "https://aitoolreport.com/feed",
        # ... 5~10개
    ])
    raw += analyze_internal_searches()  # PG 쿼리

    scored = llm_score_topics(raw)  # 상위 20개

    with SessionLocal() as db:
        for t in scored:
            db.add(Topic(
                source=t["source"], raw_topic=t["raw"],
                normalized_topic=t["normalized"], score=t["score"]
            ))
        db.commit()

    push_to_jh(scored[:20])
```

### 4.2 블로그 초안 생성 (Claude API)

```python
# apps/api/src/vaultix_api/services/blog_draft.py
import httpx
from vaultix_api.settings import settings


SYSTEM_PROMPT = """당신은 한국 마케팅·기획 직장인을 위한 AI 활용 가이드 블로거입니다.
원칙:
- 친근하지만 격식 있는 어조 (~해요, ~할 수 있어요)
- 1500~2000자
- H2 3~5개, H3 옵션
- 구체적 수치·도구명·단축키 포함
- 마지막에 "정리" 섹션
- 본문 안에 인용 가능한 자료가 있으면 [참고: 출처명](URL) 형식
- AI 글 위장 X — 솔직하게 'AI로 만들었다'고 시작하지는 말 것 (관점이 사람의 것)
"""


async def generate_draft(topic: str, category: str, references: list[dict]) -> str:
    refs_text = "\n".join(f"- {r['title']}: {r['snippet']} ({r['url']})" for r in references)
    user_prompt = f"""주제: {topic}
카테고리: {category}
참고 자료:
{refs_text}

위 주제로 블로그 글 초안을 작성하세요. 마크다운 출력."""

    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 3000,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_prompt}],
            },
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"]
```

### 4.3 통합·다듬기 (인사이트 + 초안 → 최종)

```python
# apps/api/src/vaultix_api/services/blog_integrate.py
async def integrate(draft: str, insight: str) -> str:
    user_prompt = f"""다음은 한국 직장인 페르소나의 AI 활용 블로그 초안과 작성자(JH) 본인의 본업 인사이트입니다.

초안:
{draft}

작성자 인사이트:
{insight}

다음 원칙으로 통합하세요:
1. 인사이트의 본업 사례·수치를 본문 적절한 위치에 자연스럽게 삽입
2. 작성자 어조에 맞춰 톤 조정 (친근한 프로)
3. 중복·모순 정리
4. 인용 출처는 유지
5. 길이는 초안의 ±20%

최종 본문만 출력 (설명 X, 마크다운만)."""
    # ... Claude 호출
```

### 4.4 인라인 자산 카드 (remark 플러그인)

```ts
// apps/web/src/lib/remark-asset-card.ts
import { visit } from "unist-util-visit";

export function remarkAssetCard() {
  return (tree: any) => {
    visit(tree, "text", (node, index, parent) => {
      const re = /\[\[asset:(\d+)\]\]/g;
      const matches = [...node.value.matchAll(re)];
      if (!matches.length) return;
      // text를 split해서 mdxJsxFlowElement로 치환
      const parts: any[] = [];
      let last = 0;
      for (const m of matches) {
        if (m.index! > last) parts.push({ type: "text", value: node.value.slice(last, m.index) });
        parts.push({
          type: "mdxJsxFlowElement",
          name: "AssetInlineCard",
          attributes: [{ type: "mdxJsxAttribute", name: "id", value: m[1] }],
          children: [],
        });
        last = m.index! + m[0].length;
      }
      if (last < node.value.length) parts.push({ type: "text", value: node.value.slice(last) });
      parent.children.splice(index, 1, ...parts);
    });
  };
}
```

### 4.5 .env 추가분

```dotenv
# Phase 3
ANTHROPIC_API_KEY=
SERPAPI_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
PINTEREST_ACCESS_TOKEN=
PINTEREST_BOARD_MAP={"business":"abc123","illustration":"def456"}
ADSENSE_PUBLISHER_ID=
COUPANG_AFFILIATE_ID=
WHISPER_MODE=local        # local | openai
OPENAI_API_KEY=           # whisper용 (선택)
```

---

## 5. 테스트 계획

### 5.1 메타 콘텐츠 파이프라인 E2E

| 시나리오 | 검증 |
|---------|------|
| 토픽 발굴 → Telegram 푸시 → 승인 | 5분 안에 인박스 도착 |
| 승인된 토픽 → 30분 내 초안 생성 | OK |
| 인사이트 5개 불릿 입력 → 통합 → 최종 | 톤·길이 적절 |
| 발행 버튼 → 다국어 번역 24시간 내 | en/ja도 published_at 세팅 |
| 본문 안 `[[asset:1234]]` → 자산 카드 렌더 | OK |

### 5.2 AdSense 가이드라인 검증

- 위반 항목 사전 제거: pop-up, autoplay, 가짜 다운로드 버튼, 다운로드 버튼 옆 광고
- ads.txt 정상 노출
- 도메인 3개월+ 보유
- 30편+ original content

### 5.3 Pinterest 발행 검증

- 자동 발행 1주 후 인상수·클릭수 0이 아닌지
- 핀 → 사이트 유입 트래픽 Plausible로 확인

---

## 6. 리스크 & 대응

| 리스크 | 가능성 | 영향 | 대응 |
|--------|:---:|:---:|------|
| AdSense 거절 (저품질·정책 위반) | 中 | 高 | 사전 체크리스트 100% 통과 후 신청, 거절 시 90일 보강 |
| 블로그 초안 LLM 비용 폭증 | 中 | 中 | 월 $30 캡, 80% 도달 시 알림 |
| 콘텐츠 표절·저작권 분쟁 | 低 | 高 | 인용 출처 명시, AI 출처 표기, 발견 즉시 수정 |
| Pinterest 정책 위반 (반복 핀) | 中 | 中 | 일 10개 한도, 핀당 description 다양화 |
| 본업 클라이언트 사례 노출 (계약 위반) | 中 | 高 | 고객명·수치 익명화, 발행 전 본인 검토 필수 |
| 토픽 발굴이 저질 (반복적·뻔한 주제) | 中 | 中 | LLM 점수화 + JH 큐레이션 5분 |
| 뉴스레터 스팸 분류 | 中 | 中 | SPF/DKIM/DMARC, mail-tester.com 90+ 점수 |
| Whisper 한국어 인식률 | 中 | 低 | 5분 음성 처리 시간 측정, large 모델 사용 |
| 인사이트 추가 자체가 burnout (시간 부담) | 中 | 中 | 글당 음성 5분 캡, 못 채우면 AI 일반 글로 발행 |
| 광고 수익 미미 (월 1만 원 미만) | 中 | 低 | Phase 4에서 PV 키우는 데 집중, Ezoic 검토 |

---

## 6.5 v0.4 보강 작업 (99B + A7 반영)

### 6.5.1 새 WBS 항목

| ID | 그룹 | 작업 | 결정 ID |
|----|------|------|---------|
| W2.5 | 토픽 발굴 | 토픽 점수화 모델을 Gemini 2.5 Pro로 라우팅 (A7 §2 #6) | A7 D-13·D-15 |
| W3.5 | 초안 생성 | 블로그 초안을 Claude Opus 4.6으로 라우팅 (Haiku 폐기) | A7 D-13·D-15 |
| W3.6 | 초안 생성 | 인사이트 통합도 Claude Opus 4.6 사용 | A7 |
| W4.5 | DB | 마이그레이션 0020 — pgvector 활성화 + assets/blog_posts.embedding 인덱스 | T-14 |
| W4.6 | 매칭 | sentence-transformers(384d) 임베딩 워커 추가 + 모든 기존 자산·블로그 백필 | T-14 |
| W4.7 | UI | 자산 상세 페이지에 "관련 가이드/블로그 3개" 컴포넌트 (임베딩 기반) | T-14 |
| W4.8 | UI | 블로그 페이지에 "관련 자산 12개 그리드" 컴포넌트 | T-14 |
| W5.5 | SEO | 본문 내 키워드 매칭 → 자산 4~6개 자동 삽입 미들웨어 (LLM 후처리) | T-13 |
| W5.6 | SEO | schema.org JSON-LD: Article + HowTo + FAQPage 적용 | T-13 |
| W6.5 | UI | 어드민 대시보드 v2 — AdSense API 연동 + Top/Worst 자산 + LLM 호출 위젯 | T-12 |
| W6.6 | UI | 모바일 PWA 큐레이션 정식 출시 (Phase 2 도입분 안정화) | T-12 |
| W7.5 | B2B | 한국 디자인 에이전시·중소기업 30곳 콜드메일 + 응답 분석 | B-14 |
| W7.6 | C2PA | C2PA Content Credentials 도입 검토 + PoC | T-15 |
| W8.5 | 컨텐츠 | ComfyUI 특수 워크플로우 2종 추가: `style_lora_korean`, `inpaint_iterative` | D-14 |
| W8.6 | 컨텐츠 | 큐레이션 인박스에서 "발전 가능" 점수 자산 자동 시리즈화 트리거 | D-14·B-11 |

### 6.5.2 환경변수 변경

```dotenv
# Phase 3 추가 (v0.4)
ADSENSE_PUBLISHER_ID=
ADSENSE_API_KEY=                        # 대시보드 v2 광고 수익 위젯용
SENTENCE_TRANSFORMERS_MODEL=paraphrase-multilingual-MiniLM-L12-v2
PGVECTOR_EXTENSION_VERSION=0.7.0
```

---

## 7. Phase 4 진입 조건

- [ ] §1.2 완료 조건 모든 체크박스 ✅
- [ ] AdSense 승인
- [ ] 월 PV 5,000+ (Plausible 기준 1주일 평균)
- [ ] 가입 사용자 200+
- [ ] 메타 콘텐츠 자동 파이프라인 주 2편 정상 발행 4주 연속
- [ ] 첫 광고 수익 발생 (단 1원이라도)
- [ ] 본업 사례 익명화 검수 절차 정착
- [ ] **(v0.4)** B-14 B2B 콜드메일 30건 발송 + 응답 분석 보고서 작성 → Phase 4에서 B2B 본격화 여부 결정 가능
- [ ] **(v0.4)** 자산↔가이드 임베딩 매칭 정상 작동 (자산 페이지 평균 추천 클릭률 측정)
- [ ] **(v0.4)** 어드민 대시보드 v2 모든 위젯 작동 (15개 위젯)
- [ ] **(v0.4)** ComfyUI 특수 워크플로우 4종 도입 완료 (consistent_character, controlnet_pose, style_lora_korean, inpaint_iterative)
- [ ] **(v0.4)** schema.org JSON-LD 모든 페이지 적용 + Search Console "강화 결과" 인식

---

## 8. 다음 액션

1. Phase 2 §7 진입 조건 충족 시 본 W1 착수
2. 사전 30편 작성은 Phase 1·2 진행 중 틈틈이 토픽 메모해두면 W5 부담 ↓
3. AdSense는 도메인 등록 후 3개월+ 경과 필요 — Phase 2 W1 도메인 등록일 기준으로 W7 가능 시점 자동 결정
4. **(v0.4)** B2B 콜드메일(W7.5)은 트래픽이 부족해도 가설 검증 가능 — Phase 4 B2B 트랙 결정의 근거가 됨
5. **(v0.4)** 영어 다국어는 Phase 4에서 추가 (D-11) — 본 Phase 3 메타 콘텐츠는 한·일만 발행

