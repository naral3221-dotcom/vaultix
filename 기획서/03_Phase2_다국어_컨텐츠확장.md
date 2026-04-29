# Phase 2 — 일본어 출시 + 컨텐츠 타입 확장 상세 기획서

> **목적**: 한국어 단일 이미지 사이트 → 한국어+일본어 2개 언어 + PPT/SVG/DOCX 3개 컨텐츠 타입 추가. 영어는 Phase 4 이후로 미룬다.
> **선행**: Phase 1 §7 진입 조건 모두 통과 / 도메인 등록 완료
> **작성일**: 2026-04-27
> **v0.4 기준**: D-11에 따라 다국어 우선순위는 한 → 일 → 영이다. Phase 2의 공개 언어는 `ko`, `ja`만이다.

---

## 1. 목표 & 완료 조건

### 1.1 목표

1. 한국어 단일 → **한·일 2개 언어 운영** (UI + 자산 메타 + 라이선스/약관)
2. 이미지 단일 → **이미지 + PPT + SVG + DOCX** 4개 타입 동시 운영
3. **OAuth 로그인** (Google, Kakao) 추가로 가입 마찰 ↓
4. **즐겨찾기 · 컬렉션** 추가로 재방문 동기 ↑
5. **환영 이메일 시퀀스** (Listmonk) 가동

### 1.2 완료 조건 (체크리스트)

**다국어**
- [ ] next-intl 셋업 + `/ko /ja` 서브디렉터리 라우팅
- [ ] 모든 UI 텍스트(약 200~300 키) ko/ja JSON 번역 (수동) + i18next-parser로 누락 자동 검증
- [ ] DeepL API 연동 + 자산 메타데이터 ko → ja 자동 번역 (배치 + 신규)
- [ ] hreflang 태그 모든 페이지에 정확히 출력
- [ ] 언어별 sitemap (`sitemap-ko.xml` 등) + 인덱스 sitemap에 포함
- [ ] 라이선스/약관/Privacy 한·일 수동 번역 본문 발행

**컨텐츠 타입 확장**
- [ ] `assets.asset_type IN ('image','pptx','svg','docx')` 동시 운영
- [ ] PPT 생성 워커 + LibreOffice headless 미리보기
- [ ] SVG 생성 워커 + svgo lint + 브라우저 렌더 검증
- [ ] DOCX 이력서 생성 워커 + docx → PDF 미리보기
- [ ] 큐레이션 인박스가 4개 타입을 다 처리 가능 (타입별 미리보기 컴포넌트)
- [ ] 일 자동 발행 100개+ (이미지 50, 그 외 합계 50+) × 7일

**인증·즐겨찾기**
- [ ] Google OAuth + Kakao OAuth 가입·로그인 동작
- [ ] OAuth 첫 로그인 시 이메일 자동 인증 (Google·Kakao 자체 인증된 이메일)
- [ ] 즐겨찾기 토글 + `/account/favorites` 페이지

**이메일 시퀀스**
- [ ] Listmonk + Resend 이중 구성 (트랜잭션은 Resend, 마케팅은 Listmonk)
- [ ] 환영 시퀀스 4편 (D+0/+3/+7/+14) 발송 자동화
- [ ] 더블 옵트인 동작

**도메인·SEO**
- [ ] Vaultix 정식 도메인 등록 완료 (`vaultix` 기반 후보 우선)
- [ ] `https://www.<domain>.com` + `https://<domain>.com` 둘 다 같은 사이트로 작동 (canonical 설정)
- [ ] Google Search Console + Bing Webmaster 등록 + sitemap 제출
- [ ] OG 이미지 자동 생성 (자산별 1200×630)

---

## 2. 작업 분해 (WBS)

> W1~W8은 묶음 단위 + 의존성 순서일 뿐 일정 약속이 아닙니다 (D-9).

### W1 — 도메인 + 다국어 라우팅 인프라

- [ ] **1.1** 도메인 등록 (Cloudflare Registrar 권장 — 원가, 무료 WHOIS privacy)
- [ ] **1.2** Cloudflare DNS A 레코드 → main-hub IP, AAAA → IPv6
- [ ] **1.3** 시스템 nginx server_name 변경, certbot으로 정식 도메인 인증서 발급
- [ ] **1.4** B1 §15.2 도메인 톤 미세조정 적용 (선택한 도메인에 따라 컬러 채도/라운드 미세조정)
- [ ] **1.5** next-intl 설치 + 미들웨어 (`apps/web/src/middleware.ts`)
- [ ] **1.6** `app/[locale]/(public)/...`, `app/[locale]/(admin)/...` 디렉토리 재구성
- [ ] **1.7** 언어 감지 정책: 1) 사용자 명시 토글 > 2) 쿠키 > 3) Accept-Language > 4) 기본 ko

### W2 — UI 번역 + 라이선스/약관 다국어

- [ ] **2.1** 모든 UI 텍스트를 `messages/ko.json`, `ja.json`으로 추출 (i18next-parser)
- [ ] **2.2** ko 번역(원본) 점검·정리 + ja 1차 번역 (DeepL)
- [ ] **2.3** ja 사람 검수 (JH 본인 + 일본어 검수 가능 지인/외부 검수 1명) — 가벼운 마이크로카피만 검증
- [ ] **2.4** 라이선스 본문(A5 §1) 일본어 번역 (수동, 법적 정확성)
- [ ] **2.5** Privacy/Terms/About 일본어 번역
- [ ] **2.6** Header의 LangSwitcher 컴포넌트 (B1 §7.3 `LangSwitcher`)
- [ ] **2.7** Footer 언어 토글
- [ ] **2.8** 누락 키 자동 검증 CI (i18next-parser + diff)

### W3 — 자산 메타데이터 다국어

- [ ] **3.1** Alembic 0005 마이그레이션: `asset_translations` 생성 + 기존 `assets.title_ko` 데이터를 `asset_translations(locale='ko')`로 이전 (인서트, 원본 컬럼 유지)
- [ ] **3.2** DeepL 어댑터 (`adapters/deepl.py`) — 글자수 caching·중복 방지
- [ ] **3.3** `translate_asset_meta` Celery 태스크: 신규 자산 발행 시 자동 큐잉, 기존 자산 일괄 백필 배치
- [ ] **3.4** 자산 응답 API에 `Accept-Language` / `?locale=` 기반 응답 본문 자동 선택
- [ ] **3.5** `asset_translations.source` 추적 (auto/manual) + 어드민에서 수동 수정 가능
- [ ] **3.6** PG FTS 인덱스를 locale별로 추가 (en, ja)

### W4 — hreflang + sitemap + SEO

- [ ] **4.1** 모든 페이지에 hreflang 태그 자동 출력 (next-intl 헬퍼)
- [ ] **4.2** sitemap 분리: `sitemap-ko.xml`, `sitemap-ja.xml`, image-sitemap도 동일
- [ ] **4.3** `/robots.txt`에 sitemap 인덱스 명시
- [ ] **4.4** Schema.org `inLanguage` 속성 추가
- [ ] **4.5** OG 이미지 자동 생성 (`@vercel/og` 또는 자체 SSR PNG) — 자산별 1200×630
- [ ] **4.6** Google Search Console 등록 + sitemap 제출 → 인덱싱 시작 모니터링

### W5 — OAuth + 즐겨찾기

- [ ] **5.1** Auth.js v5에 Google Provider 추가 (Google Cloud Console에서 OAuth client 발급)
- [ ] **5.2** Auth.js v5에 Kakao Provider 추가 (Kakao Developers)
- [ ] **5.3** OAuth 첫 가입 시 자동 이메일 인증 (provider가 인증한 이메일은 verified로)
- [ ] **5.4** OAuth 계정과 기존 비밀번호 계정 병합 정책 (같은 이메일 → 같은 사용자)
- [ ] **5.5** Alembic 0006 마이그레이션: `oauth_accounts`, `favorites`
- [ ] **5.6** 즐겨찾기 토글 컴포넌트 + `/account/favorites` 페이지
- [ ] **5.7** assets.favorite_count 트리거 검증

### W6 — PPT 생성 파이프라인

- [ ] **6.1** PPT 워커 추가 (`celery-pptx`)
- [ ] **6.2** PPT 생성 어댑터: A7 LLM 라우터가 슬라이드 구조 JSON 생성 → python-pptx로 .pptx 빌드
- [ ] **6.3** PPT 템플릿 5종 사전 작성 (사업제안 / 분기보고 / 신제품 / 사례발표 / 트레이닝)
- [ ] **6.4** LibreOffice headless로 .pptx → PNG 미리보기 (4매 정도, 슬라이드 1·2·5·N)
- [ ] **6.5** PPT prompt_templates 시드 20개 (A4)
- [ ] **6.6** 큐레이션 인박스에 PPT 미리보기 컴포넌트 (PNG 4매 갤러리)
- [ ] **6.7** 검증 단계: pptx 파일 무결성 (open 가능 여부, 슬라이드 수 ≥ 5)
- [ ] **6.8** 다운로드 시 .pptx + .pdf(LibreOffice 변환) 둘 다 제공

### W7 — SVG 인포그래픽 + DOCX 이력서

- [ ] **7.1** SVG 워커 (`celery-svg`)
  - LLM이 SVG 코드 생성 → svgo로 lint·최적화 → Playwright로 헤드리스 렌더 검증 (보이지 않는 콘텐츠 감지)
  - 인포그래픽 5종 템플릿 (프로세스 / 비교 / 타임라인 / 통계 / 조직도)
- [ ] **7.2** DOCX 워커 (`celery-docx`)
  - 이력서 / 자기소개서 / 보고서 표지 3종 템플릿
  - LLM 구조 → python-docx → LibreOffice headless로 PDF 미리보기
  - 카테고리: 신입 / 경력 / 디자인 직군 / 기획 직군 / 영업 직군
- [ ] **7.3** 큐레이션 인박스 통합: 타입별 미리보기 컴포넌트 (이미지·PPT·SVG·DOCX)
- [ ] **7.4** 검증·점수 단계 통합 (각 타입별 워커 → 같은 image_post 큐로 후속)

### W8 — 컬렉션 + 환영 이메일 시퀀스 + 안정화

- [ ] **8.1** Alembic 0007: `collections`, `collection_items`
- [ ] **8.2** `/collections/[slug]` 페이지 + 어드민 컬렉션 관리
- [ ] **8.3** 홈 히어로 아래 "이번 주 큐레이션" 4개 컬렉션 노출 (B2 §4.1 구체화)
- [ ] **8.4** 첫 컬렉션 4개 만들기 (직접 큐레이션, 자산 20~30개씩)
- [ ] **8.5** Listmonk 셋업 + Resend SMTP 연동 (송신 도메인 SPF/DKIM)
- [ ] **8.6** 환영 시퀀스 4편 본문 작성 + 트리거 자동화
- [ ] **8.7** 더블 옵트인 흐름
- [ ] **8.8** 통합 테스트: 영어 사용자가 가입 → DeepL로 ja 메타 자동 번역된 자산 다운로드까지 시나리오
- [ ] **8.9** Phase 3 진입 전 회고 (1주)

---

## 3. 기술 결정사항

### 3.1 결정 1 — i18n 라이브러리

**선택**: **next-intl** (App Router 친화)

| 옵션 | 장점 | 단점 |
|------|------|------|
| next-intl ⭐ | App Router 지원, 미들웨어 라우팅 깔끔 | 비교적 신생 |
| next-i18next | 생태계 큼 | App Router 지원 약함 |

### 3.2 결정 2 — DeepL vs Google Translate

**선택**: **DeepL Free → 한도 초과 시 Pro**

| 옵션 | 장점 | 단점 |
|------|------|------|
| DeepL ⭐ | 한·일 번역 품질 안정적 | 월 50만자 무료 → 자산 5만개+ 시 Pro 필요 |
| Google Translate | 더 많은 언어 | 한·일 품질 살짝 떨어짐, 비용 비슷 |

근거: 자산 메타는 짧음(평균 200자) → 50만자 = 자산 2500개 번역. Phase 2 종료까지 충분.

### 3.3 결정 3 — PPT 생성 모델

**선택**: **A7 LLM 라우터 (구조 JSON) + python-pptx**

| 옵션 | 장점 | 단점 |
|------|------|------|
| A7 LLM 라우터 ⭐ | 플래그십 모델 품질, 폴백·로깅 일원화 | 외부 API 의존 |
| 단일 provider API | 구현 단순 | 장애·품질 비교·교체가 어려움 |
| 로컬 Qwen | 외부 의존 낮음 | D-13으로 폐기 |

근거: D-13/D-15에 따라 로컬 LLM은 쓰지 않는다. PPT 구조 JSON도 `TaskType`을 분리해 A7 라우터를 통과시키고, 응답은 JSON schema 검증 후 python-pptx로 빌드한다.

### 3.4 결정 4 — LibreOffice headless 컨테이너

**선택**: **별도 컨테이너 `vaultix-libreoffice`** (`linuxserver/libreoffice` 또는 자체 빌드)

- PPT/DOCX → PNG/PDF 변환 전용
- 워커가 HTTP API로 호출 (간단한 FastAPI 래퍼)
- 시작 시간 길어 stateful 컨테이너 (재시작 최소화)

### 3.5 결정 5 — Kakao OAuth

**선택**: **Phase 2 W5에 추가**

- 한국 사용자 가입 마찰 감소 큼
- Kakao Developers에서 사업자 등록 없이 200/일 한도 OK (Phase 2 베타에 충분)
- 정식 검수는 Phase 3 직전

### 3.6 결정 6 — 기존 ko 데이터 마이그레이션

**선택**: **non-destructive 마이그레이션**

- `assets.title_ko` 등 기존 컬럼 유지 (검색 색인용 캐시 역할)
- 모든 row를 `asset_translations(locale='ko')`에 INSERT
- 신규 자산은 `assets.title_ko` + `asset_translations(ko)` 둘 다 입력
- Phase 4 이후에 필요 없으면 `assets.*_ko` 컬럼 삭제 검토

---

## 4. 코드/설정 골격 (Phase 2 추가분)

### 4.1 docker-compose 추가분

```yaml
  celery-pptx:
    image: ghcr.io/${GH_OWNER}/vaultix-api:${IMAGE_TAG}
    container_name: vaultix-celery-pptx
    restart: unless-stopped
    networks: [internal]
    depends_on: [redis, postgres, libreoffice]
    environment:
      DATABASE_URL: ...
      REDIS_URL: ...
      LIBREOFFICE_URL: http://libreoffice:8400
    volumes:
      - /var/lib/vaultix/assets:/data/assets
    command: celery -A vaultix_api.workers.celery_app worker -Q pptx -c 2

  celery-svg:
    # 같은 이미지, 큐만 다름
    command: celery -A vaultix_api.workers.celery_app worker -Q svg -c 2

  celery-docx:
    command: celery -A vaultix_api.workers.celery_app worker -Q docx -c 2

  libreoffice:
    image: linuxserver/libreoffice:latest
    container_name: vaultix-libreoffice
    restart: unless-stopped
    networks: [internal]
    environment:
      PUID: 1001
      PGID: 1001
      TZ: Asia/Seoul
    volumes:
      - /var/lib/vaultix/lo-temp:/tmp
    # FastAPI 래퍼는 별도 컨테이너 또는 같은 이미지 안에서 sidecar
```

### 4.2 next-intl 미들웨어

```ts
// apps/web/src/middleware.ts
import createMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

export default createMiddleware(routing);

export const config = {
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"]
};
```

```ts
// apps/web/src/i18n/routing.ts
import { defineRouting } from "next-intl/routing";

export const routing = defineRouting({
  locales: ["ko", "ja"],
  defaultLocale: "ko",
  localePrefix: "always"  // /ko/... /ja/...
});
```

### 4.3 PPT 생성 어댑터 (개요)

```python
# apps/api/src/vaultix_api/adapters/pptx_gen.py
from pptx import Presentation
from pptx.util import Inches, Pt
from vaultix_api.services.llm_router import TaskType, call_llm_json


SLIDE_STRUCTURE_PROMPT = """다음 주제로 5~10장 분량의 비즈니스 PPT 슬라이드 구조를 JSON으로 작성하세요.
형식:
{
  "title": "...",
  "slides": [
    {"layout": "title", "title": "...", "subtitle": "..."},
    {"layout": "section", "title": "..."},
    {"layout": "bullets", "title": "...", "bullets": ["...", "...", "..."]},
    {"layout": "stat", "title": "...", "stat_value": "82%", "stat_label": "..."},
    ...
  ]
}
JSON 외 텍스트 금지. 슬라이드 5~10개. bullets는 슬라이드당 3~5개.
"""


async def generate_pptx_structure(topic: str) -> dict:
    return await call_llm_json(
        task=TaskType.PPT_STRUCTURE,
        system=SLIDE_STRUCTURE_PROMPT,
        user=topic,
        timeout_s=60,
    )


def build_pptx(struct: dict, template_path: str | None = None) -> bytes:
    prs = Presentation(template_path) if template_path else Presentation()
    for s in struct["slides"]:
        if s["layout"] == "title":
            slide = prs.slides.add_slide(prs.slide_layouts[0])
            slide.shapes.title.text = s["title"]
            slide.placeholders[1].text = s.get("subtitle", "")
        elif s["layout"] == "bullets":
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            slide.shapes.title.text = s["title"]
            tf = slide.placeholders[1].text_frame
            tf.text = s["bullets"][0]
            for b in s["bullets"][1:]:
                p = tf.add_paragraph(); p.text = b
        # ... 다른 layout
    import io
    buf = io.BytesIO(); prs.save(buf)
    return buf.getvalue()
```

### 4.4 SVG 검증 (svgo + Playwright)

```python
# apps/api/src/vaultix_api/services/svg_validator.py
import asyncio
from pathlib import Path


async def validate_svg(svg_text: str, dest: Path) -> dict:
    """svgo lint + Playwright 렌더로 텅 빈 SVG 감지."""
    # 1) svgo (Node.js CLI)
    proc = await asyncio.create_subprocess_exec(
        "npx", "svgo", "--input", "-", "--output", "-",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate(svg_text.encode())
    if proc.returncode != 0:
        return {"ok": False, "reason": f"svgo failed: {stderr[:200]}"}

    optimized = stdout.decode()
    dest.write_text(optimized)

    # 2) Playwright 헤드리스 렌더 → 픽셀 통계
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1024, "height": 1024})
        await page.set_content(f'<html><body><div style="display:inline-block">{optimized}</div></body></html>')
        png = await page.screenshot()
        await browser.close()

    # 단순 휴리스틱: PNG 파일 크기로 빈 SVG 감지
    if len(png) < 5_000:
        return {"ok": False, "reason": "rendered SVG is suspiciously small (likely empty)"}

    return {"ok": True, "preview_png": png, "optimized": optimized}
```

### 4.5 DeepL 어댑터

```python
# apps/api/src/vaultix_api/adapters/deepl.py
import httpx
from vaultix_api.settings import settings


class DeeplError(Exception): pass


async def translate(text: str, target: str, source: str = "KO") -> str:
    """target은 ISO 639-1 또는 DeepL 코드 (EN-US, JA 등)."""
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(
            "https://api-free.deepl.com/v2/translate",
            data={
                "auth_key": settings.deepl_api_key,
                "text": text,
                "source_lang": source,
                "target_lang": target,
            },
        )
        if r.status_code != 200:
            raise DeeplError(f"deepl {r.status_code} {r.text[:200]}")
        return r.json()["translations"][0]["text"]
```

### 4.6 .env 추가분

```dotenv
# Phase 2
DEEPL_API_KEY=
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
KAKAO_OAUTH_CLIENT_ID=
KAKAO_OAUTH_CLIENT_SECRET=
LISTMONK_URL=http://listmonk:9000
LISTMONK_ADMIN_USER=vaultix
LISTMONK_ADMIN_PASSWORD=
```

---

## 5. 테스트 계획

### 5.1 i18n 테스트

| 시나리오 | 검증 |
|---------|------|
| Accept-Language: ja → 자동 /ja로 라우팅 | OK |
| 사용자 LangSwitcher → ja 선택 → 쿠키 저장 → 재방문 시 /ja 유지 | OK |
| 모든 페이지에 hreflang 2개 + x-default 정확 출력 | OK |
| 누락된 i18n 키 (ja에 없음) → CI 경고 | OK |

### 5.2 컨텐츠 타입 통합 테스트

| 시나리오 | 검증 |
|---------|------|
| 4개 타입 동시 발행 (이미지 50, PPT 5, SVG 5, DOCX 2) × 7일 | OK |
| PPT 다운로드 후 PowerPoint에서 정상 열림 | OK |
| SVG 다운로드 후 Figma/Adobe Illustrator에서 정상 열림 | OK |
| DOCX 다운로드 후 한컴오피스/MS Word에서 정상 열림 | OK |
| 큐레이션 인박스에서 4개 타입 모두 미리보기 정상 | OK |

### 5.3 OAuth 테스트

- Google 신규 가입 → email_verified 자동 true
- 같은 이메일을 password로 가입한 사용자 → OAuth 연결 시 같은 user_id로 병합

### 5.4 메타데이터 번역 백필 테스트

- 기존 ko 자산 100개 → DeepL 번역 → asset_translations(en) 100건 INSERT
- 응답 API에 `?locale=en` 시 영문 메타 반환 확인

---

## 6. 리스크 & 대응

| 리스크 | 가능성 | 영향 | 대응 |
|--------|:---:|:---:|------|
| 도메인 이름 후회 (등록 후 변경 어려움) | 中 | 高 | 등록 전 1주간 매일 적어보고 입에 익는지 점검 |
| DeepL Free 50만자 빠르게 소진 | 中 | 中 | 사용량 모니터, 80% 도달 시 Pro 전환 ($25/월) |
| OAuth provider 정책 변경 | 低 | 中 | 두 provider 모두 사용으로 분산 |
| Kakao OAuth 검수 보류 | 中 | 中 | Phase 2 W5에 미리 신청, 거절 시 password 가입에 의존 |
| LibreOffice 변환 실패 (특수 폰트 등) | 中 | 中 | docx/pptx에 표준 폰트만 사용, fallback 폰트 명시 |
| PPT 구조 LLM JSON 파싱 실패 | 中 | 中 | 재시도 3회 + 실패 자산 폐기 + 프롬프트 개선 루프 |
| 환영 메일 스팸 분류 | 中 | 中 | SPF/DKIM/DMARC 정확히 셋업, mail-tester.com 점검 |
| 기존 사용자 마이그레이션 시 다운타임 | 低 | 中 | non-destructive 마이그레이션, 무중단 배포 |
| 일본어 사용자 0명 (의미 없는 작업) | 中 | 低 | Plausible로 모니터, Release 2 이후 6개월간 의미 없으면 backlog |
| svgo 충돌 (LLM이 비표준 SVG 생성) | 中 | 中 | svgo 옵션 완화 + 검증 단계에서 reject |

---

## 6.5 v0.4 보강 작업 (99B + A7 반영)

### 6.5.1 우선 의사결정 (착수 전)

- [ ] **D-11 다국어 우선순위 확정**: v0.4에서 한 → 일 → 영으로 변경됨. 본 Phase 2는 **한·일** 출시, 영어는 Phase 4로 미룸. (기존 v0.3은 한·영·일 동시였음)
  - next-intl locale 설정: `['ko','ja']` (Phase 4에 `'en'` 추가)
  - DeepL 호출은 ko→ja 우선

### 6.5.2 새 WBS 항목

| ID | 그룹 | 작업 | 결정 ID |
|----|------|------|---------|
| W1.5 | 도메인 | 도메인 톤 검증 + 등록 (Phase 1 W8에서 미진행 시) | (기존) |
| W2.5 | i18n | locale을 `['ko','ja']`로 한정 (영어 제외) — 영어 코드는 Phase 4 추가 | D-11 |
| W3.5 | DB | A1 §17 v0.4 보강 테이블 마이그레이션 0019 (asset_recipes) | B-11 |
| W4.5 | UI | **자산 상세 페이지 레시피 섹션** + 워크플로우 다운로드 | B-11 ★★★ |
| W4.6 | UI | `/today` `/log` 페이지 발행 (Phase 1에서 골격만 만든 경우 전체 구현) | B-13 |
| W4.7 | UI | `/account/delete-account` `/account/export-data` GDPR 페이지 | B-10 |
| W4.8 | UI | 가입 시 만 16세 미만 차단 (생년월일 또는 체크박스) | B-10 |
| W4.9 | UI | EU IP 쿠키 동의 배너 (Cloudflare Geo 분기) | B-10 |
| W4.10 | UI | `/admin/inbox-mobile` 모바일 PWA 큐레이션 (스와이프) | T-12·D-12 |
| W5.5 | i18n | A5 §6 신고 절차 + §7 레시피 CC0 일본어 번역 | B-09·B-11 |
| W6.4 | 컨텐츠 | ComfyUI 특수 워크플로우 2종 도입: `consistent_character`, `controlnet_pose` | D-14 |
| W6.5 | 컨텐츠 | 어드민 자산 상세에 "시리즈로 만들기" / "포즈 변형" 트리거 버튼 | D-14·B-11 |
| W7.5 | SEO | long-tail 키워드 200개 매핑 시트 (Google Sheets) | T-13 |
| W7.6 | SEO | 경쟁 사이트 벤치마크 보고서 (Pixabay/Unsplash/미리캔버스/FreePik/망고보드) | T-13 |
| W7.7 | SEO | schema.org JSON-LD 컴포넌트 (자산·블로그·가이드·FAQ) | T-13 |
| W7.8 | a11y | axe-core CI 통합 + 색 대비 점검 + 키보드 내비게이션 검증 | B-10 |

### 6.5.3 환경변수 변경 (.env)

```dotenv
# Phase 2 추가 (v0.4)
DEEPL_API_KEY=                       # 한→일 번역 (한→영은 Phase 4까지 미사용)
GEO_DETECTION_ENABLED=true           # GDPR 쿠키 배너용 EU IP 분기
COMFY_HOST=http://100.x.x.x:8188     # 특수 워크플로우용 (Phase 2부터 활용)
```

### 6.5.4 폐기되는 v0.3 작업

| 폐기 작업 | 폐기 사유 |
|----------|----------|
| 영어 locale `'en'` Phase 2 추가 | D-11 — 영어는 Phase 4로 |
| LibreOffice 컨테이너 PPT 변환 (이미 있으면 유지) | (변경 없음 — 다만 LLM 호출 부분만 외부 API로) |

---

## 7. Phase 3 진입 조건

- [ ] §1.2 완료 조건 모든 체크박스 ✅
- [ ] 일 자동 발행 100개+ × 7일
- [ ] 4개 컨텐츠 타입 다운로드 정상 동작 검증
- [ ] DeepL 번역(한→일) 자산 1000+ 건 누적
- [ ] OAuth 가입 사용자 5명+ (베타 확장)
- [ ] 사이트 인덱싱 페이지 100+ (Search Console 기준)
- [ ] 묶음 5의 라이선스 본문(A5) 한·일 발행 완료 (영어는 Phase 4)
- [ ] **(v0.4)** 자산 상세 페이지 레시피 섹션 작동 + 워크플로우 다운로드 검증
- [ ] **(v0.4)** ComfyUI 특수 워크플로우 2종 동작 검증 + 인박스에서 트리거 가능
- [ ] **(v0.4)** GDPR 삭제권·이동권 페이지 정상 동작
- [ ] **(v0.4)** WCAG 2.1 AA axe-core CI 0 critical 위반
- [ ] **(v0.4)** 모바일 PWA 큐레이션 작동 (오프라인 큐잉 포함)
- [ ] **(v0.4)** SEO 키워드 시트 200행 + schema.org JSON-LD 모든 자산·블로그 페이지 적용

---

## 8. 다음 액션

1. Phase 1 §7 진입 조건 충족 시 본 W1 착수
2. 도메인 등록은 W1 사전 작업 (등록 전에는 임시 도메인으로 진행 가능)
3. A5 라이선스 본문의 일본어 번역은 W2와 병행
4. **(v0.4)** D-11 다국어 우선순위(한→일) 확정 — 영어 제외 결정을 03 문서 본문에 반영
5. **(v0.4)** 레시피 공개(B-11)는 Phase 2 핵심 차별화 — W4.5 우선 처리

