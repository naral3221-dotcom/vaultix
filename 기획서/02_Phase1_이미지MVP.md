# Phase 1 — 이미지 MVP 상세 기획서

> **목적**: 사용자(직장인 박지원 페르소나)가 회원가입→이메일 인증→탐색→다운로드까지 5분/5클릭 이내에 완수할 수 있는 이미지 자산 사이트의 정식 MVP를 운영 가동한다. 동시에 일 50장 이상 이미지를 자동 생성·검증·메타데이터 부여·큐레이션·시간 분산 발행하는 백엔드 파이프라인을 가동한다.
> **선행**: Phase 0 완료 / 모든 D-1~D-19 결정 / B1·B2·A1·A2·A3·A7 작성 완료
> **작성일**: 2026-04-27
> **v0.4 기준**: Phase 1은 한국어 이미지 MVP만 구현한다. Ollama/Replicate/fal.ai는 사용하지 않는다.

---

## 1. 목표 & 완료 조건

### 1.1 목표

**공개 가능한 이미지 자산 다운로드 사이트**를 운영 가동한다.

- 정의: "공개 가능"이란 베타 초대 5명에게 URL을 줘서 가입~다운로드까지 끊김 없이 사용할 수 있는 상태.
- 컨텐츠: 이미지 자산만 (PPT/SVG/DOCX 등은 Phase 2).
- 다국어: 한국어만.
- 결제·OAuth·즐겨찾기 X (Phase 2).

### 1.2 완료 조건 (체크리스트)

**제품**
- [ ] B2 §4의 6개 페이지 모두 디자인·기능 완성 (홈/탐색/자산상세/큐레이션 인박스/계정/auth)
- [ ] B2 §1.1의 1순위 페르소나 시나리오 5분 / 5클릭 이내 완수 (3회 연속 성공)
- [ ] B2 §6의 4개 빈 상태·2개 에러 페이지 디자인 완성
- [ ] 라이트/다크 모드 전환 완성, 모든 컴포넌트 양쪽 톤 점검 완료
- [ ] 모바일(390×844) / 데스크탑(1920×1080) 양쪽에서 동선 검증

**자산 파이프라인**
- [ ] prompt_templates 시드 30+ 개 입력 완료 (이미지, 카테고리별)
- [ ] Nanobanana 이미지 어댑터 + 1회 생성 검증
- [ ] OpenAI `gpt-image-2` 폴백 어댑터 + 1회 생성 검증
- [ ] ComfyUI 데스크탑 워커는 특수 워크플로우용 헬스체크만 준비 (Phase 1 일반 생성 비중 0%)
- [ ] 일 50장 자동 생성 → 검증 → 점수 → 메타데이터 → 인박스 도착 (3일 연속)
- [ ] 큐레이션 인박스에서 키보드만으로 30분 내 50장 처리 가능

**다운로드·인증·보안**
- [ ] 이메일 인증 메일 도착 (Resend) — 5종 인박스(Gmail/Naver/Kakao/Daum/Hotmail) 도달 검증
- [ ] 시간당 30회 한도 정상 작동 (29회 안내, 31회 차단)
- [ ] signed URL 만료 검증 (5분 후, 두 번째 사용 시도 모두 차단)
- [ ] Turnstile 회원가입·다운로드 단계에서 봇 차단
- [ ] 일회용 메일 도메인 가입 차단

**운영·모니터링**
- [ ] Sentry 에러율 0.5% 미만 1주
- [ ] Plausible로 사용자 행동 추적 (랜딩→다운로드 깔때기)
- [ ] 백업 일 1회 + 1회 복원 테스트 성공
- [ ] Uptime Kuma 모든 모니터 7일 99% 이상
- [ ] 라이선스/About/Privacy/Contact 페이지 발행 (A5 본문 사용)

---

## 2. 작업 분해 (WBS)

> W1~W8은 **묶음 단위 + 의존성 순서**일 뿐 일정 약속이 아닙니다 (D-9). 각 작업은 GitHub Issue로 1:1 매핑 권장.

### W1 — DB 스키마 + 인증 골격

- [ ] **1.1** Phase 0 완료 점검 (체크리스트 8개 항목)
- [ ] **1.2** Alembic 0001 마이그레이션 작성 (A1 §3, §4, §5.1, §5.2)
  - users, email_verifications, password_resets, sessions
  - categories, tags, asset_tags
  - assets, asset_files
- [ ] **1.3** Alembic 0002, 0003, 0004 작성 (A1)
- [ ] **1.4** `alembic upgrade head` 자동화 (배포 시 entrypoint)
- [ ] **1.5** 카테고리 시드 데이터 입력 (15~20개, B2 사이트맵 참조)
- [ ] **1.6** Auth.js v5 셋업 (apps/web): credentials provider, db session adapter, sign-up/sign-in 페이지

### W2 — Assets API + 카탈로그 페이지

- [ ] **2.1** SQLAlchemy 모델 (Asset, Category, Tag, AssetFile) — A1 §16 패턴
- [ ] **2.2** Pydantic 스키마 (AssetOut, AssetListOut, AssetDetailOut) — A2 §5 응답
- [ ] **2.3** `GET /api/v1/assets` 구현 (필터·정렬·cursor) — A2 §5.1
- [ ] **2.4** `GET /api/v1/assets/{slug_or_id}` — A2 §5.2
- [ ] **2.5** `GET /api/v1/meta/categories`, `/meta/tags` — A2 §2
- [ ] **2.6** Next.js 라우트: `/`, `/explore`, `/category/[slug]`, `/asset/[slug]`
- [ ] **2.7** 컴포넌트: Header, Footer, AssetCard, MasonryGrid, FilterChips, EmptyState
- [ ] **2.8** B1 §4 컬러 변수 globals.css 적용 + 다크모드 토글
- [ ] **2.9** 폰트 셋업 (Pretendard + Inter, B1 부록 B)
- [ ] **2.10** TanStack Query 셋업 + 5.2 §5.2 캐시 키 적용

### W3 — 자산 상세 + 다운로드 흐름 ⭐

- [ ] **3.1** `POST /api/v1/downloads/{id}` — A2 §6.1
- [ ] **3.2** `GET /dl/{id}/{nonce}` X-Accel-Redirect — A2 §6.2
- [ ] **3.3** signed URL HMAC 시그니처 + Redis nonce SETEX
- [ ] **3.4** 시간당 30회 Redis INCR 한도 + 응답 헤더
- [ ] **3.5** 자산 상세 페이지 — B2 §4.3 와이어 1:1 구현
- [ ] **3.6** 다운로드 모달 (비로그인/미인증 분기) — B2 §5.1 흐름
- [ ] **3.7** 라이선스 요약 카드 + 전체 보기 토글 (A5 본문 임시 placeholder)
- [ ] **3.8** Toast 시스템 (다운로드 완료, 한도 안내)
- [ ] **3.9** "이 스타일 더 보기" — 카테고리·태그 매칭 추천 (Phase 2에서 임베딩 교체)

### W4 — 큐레이션 인박스 ⭐

- [ ] **4.1** `GET /api/v1/admin/inbox` 페이지네이션 + 미리 다음 5장 prefetch — A2 §8.1
- [ ] **4.2** approve/reject/hold/regenerate 엔드포인트 — A2 §8.1
- [ ] **4.3** admin_audit_logs 자동 기록 미들웨어
- [ ] **4.4** 어드민 페이지 라우트 `/admin/inbox` — B2 §4.4 와이어
- [ ] **4.5** 키보드 단축키 (B2 §9 표) — react-hotkeys-hook
- [ ] **4.6** 메타데이터 편집 모달 (Space 키)
- [ ] **4.7** Tailscale ALLOW 검증 — 외부 IP에서 403 / Tailscale에서 200
- [ ] **4.8** require_admin 미들웨어 (FastAPI) + 클라이언트 가드 (Next.js)

### W5 — 이미지 자동 생성 파이프라인 1단계 ⭐

- [ ] **5.1** Celery 워커 컨테이너 추가 — A3 §4.2 docker-compose
- [ ] **5.2** Nanobanana 어댑터 — A3 §5.1 (`apps/api/src/vaultix_api/adapters/nanobanana.py`)
- [ ] **5.3** OpenAI `gpt-image-2` 어댑터 — A3 §5.2 (`apps/api/src/vaultix_api/adapters/openai_image.py`)
- [ ] **5.4** ComfyUI 헬스체크 어댑터만 준비 — A3 §5.3 (특수 워크플로우는 Phase 2부터)
- [ ] **5.5** generate_primary / generate_secondary 태스크 — Nanobanana 실패·품질 미달 시 `gpt-image-2`로 승격
- [ ] **5.6** prompt_template 시드 30+ 입력 (A4 시드 데이터 참조 — 묶음 5에서 작성)
- [ ] **5.7** 매일 자정 enqueue_daily_batch (Celery beat 또는 cron) — A3 §7.1
- [ ] **5.8** 이미지 provider별 헬스체크 5분 폴 + Redis 상태 — Nanobanana/OpenAI/ComfyUI
- [ ] **5.9** 외부 API 장애·도용 의심 시 `/admin/panic`에서 호출 차단 가능하게 연결
- [ ] **5.10** `/admin/queue/status` 엔드포인트 — A3 §7.3 / A2 §8.4

### W6 — 검증·점수·메타데이터 자동 생성

- [ ] **6.1** `validate_image` 태스크: Pillow로 깨진 PNG 감지, NSFW 임계 (옵션, OpenNSFW 또는 단순 채도 휴리스틱)
- [ ] **6.2** `score_image` 태스크: CLIP 임베딩 → 카테고리 적합도 + 미적 점수 (CLIP-IQA 모델)
- [ ] **6.3** 점수 < 0.4 자동 폐기, 0.4~0.7 인박스, 0.7+ 인박스 (status='inbox', `quality_score`)
- [ ] **6.4** `generate_metadata` 태스크: A7 LLM 라우터로 한국어 title/description/alt_text + 태그 5개 자동 생성
- [ ] **6.5** 썸네일·미리보기 생성 (320px·1024px WebP) → asset_files insert
- [ ] **6.5-2** EXIF 메타데이터와 HTML meta에 AI 생성물 표시(T-15)
- [ ] **6.6** 통합 파이프라인 흐름 검증 (워크플로우 → 검증 → 점수 → 메타 → 인박스 도착, 평균 시간 측정)

### W7 — 발행 큐 + 통합 테스트

- [ ] **7.1** 승인 시 즉시 발행 X. publish_queue에 enqueue (시간 분산)
- [ ] **7.2** Celery beat: 매시간 N장 발행 (예: 시간당 4장 → 일 96장)
- [ ] **7.3** publish 시 published_at 세팅 + sitemap 자동 핑 (Google ping URL)
- [ ] **7.4** PG full-text search 인덱스 동작 검증 (한국어 검색)
- [ ] **7.5** 컨트랙트 테스트 (A2 §15) — 모든 엔드포인트 200/400/401/403/404/429
- [ ] **7.6** E2E 테스트 (Playwright): 회원가입 → 인증 → 다운로드 시나리오 자동화

### W8 — 안정화·QA·라이선스/약관·베타

- [ ] **8.1** 라이선스/About/Privacy/Contact 페이지 발행 (A5 본문 — 묶음 5)
- [ ] **8.2** Resend 트랜잭션 메일 5종 인박스 도달 검증
- [ ] **8.3** Turnstile 회원가입/다운로드 단계 적용
- [ ] **8.4** 일회용 메일 도메인 차단 목록 (10minutemail 등 ~200개)
- [ ] **8.5** 핫링크 차단 (Referer 검증, Phase 2에서 Cloudflare로 강화)
- [ ] **8.6** robots.txt + sitemap.xml + image-sitemap.xml
- [ ] **8.7** 구조화 데이터 (Schema.org ImageObject) — B2 §7.2
- [ ] **8.8** 7일 무중단 모니터링
- [ ] **8.9** 베타 5명 초대 → 시나리오 완수율 100% 검증
- [ ] **8.10** 베타 피드백 30분 인터뷰 × 5건 → 회고 문서

---

## 3. 기술 결정사항 (Phase 1 한정)

### 3.1 결정 1 — 검색 엔진

**선택**: **PostgreSQL `to_tsvector` (한국어)**

| 옵션 | 장점 | 단점 |
|------|------|------|
| PG FTS ⭐ | 의존성 없음, 인프라 단순 | 한국어 형태소 분석 약함 (영문은 OK) |
| Meilisearch | 한국어 친화, 빠름 | 별도 컨테이너 + 자원 |
| OpenSearch/Elasticsearch | 강력 | 무거움, 1인 운영 부담 |

근거: 자산 1만개까지는 PG FTS 충분. 한국어 형태소는 `pg_bigm`(trigram) 보조. Meilisearch는 Phase 2/3 PV 증가 시 검토.

### 3.2 결정 2 — 메타데이터 생성 LLM

**선택**: **A7 LLM 라우터를 통한 외부 API** (Gemini/GPT/GLM/Claude)

| 옵션 | 장점 | 단점 |
|------|------|------|
| A7 LLM 라우터 ⭐ | 모델 교체·폴백·로깅 일원화, 품질 우선 | 외부 API 의존 |
| 단일 OpenAI 호출 | 구현 단순 | 장애/품질 비교/로그 일원화 약함 |
| 자체 호스팅 LLM | 외부 의존 낮음 | D-13으로 폐기, VPS CPU 낭비 |

근거: D-13/D-15에 따라 자체 호스팅 LLM은 폐기하고 외부 플래그십 API를 품질 우선으로 사용한다. 모든 호출은 `llm_call_log`에 남겨 실패율·지연·폴백을 운영 대시보드에서 볼 수 있어야 한다.

### 3.3 결정 3 — 이미지 후처리 라이브러리

**선택**: **Pillow + pillow-avif-plugin**

- WebP/AVIF 지원
- Phase 1은 WebP만, AVIF는 Phase 2에서 추가

### 3.4 결정 4 — Celery beat 위치

**선택**: **별도 컨테이너** `vaultix-celery-beat`

- 워커와 분리 (재시작·디버깅 용이)
- 단일 인스턴스 보장 (스케줄러 중복 방지)

### 3.5 결정 5 — 슬러그 생성 전략

**선택**: **자동 생성 + 충돌 시 suffix**

- LLM이 생성한 title을 기반으로 `slugify(title) + "-" + random_short(6)`
- 영문화: `python-slugify[unidecode]` 사용 (한국어 → 로마자)

```python
from slugify import slugify
import secrets

def make_slug(title: str) -> str:
    base = slugify(title, max_length=80, word_boundary=True, save_order=True)
    if not base:
        base = "asset"
    return f"{base}-{secrets.token_hex(3)}"
```

### 3.6 결정 6 — 이미지 저장 경로 정책

```
/var/lib/vaultix/assets/
├── raw/                # 생성 직후 PNG (검증 후 published로 이동)
│   └── job_{id}.png
├── published/
│   ├── original/       # PNG 원본 (다운로드용)
│   │   └── {asset_id}.png
│   ├── webp/           # WebP 변환 (다운로드용)
│   │   └── {asset_id}.webp
│   ├── preview/        # 1024px (사이트 표시)
│   │   └── {asset_id}.webp
│   └── thumb/          # 320px (그리드)
│       └── {asset_id}.webp
└── trash/              # 폐기 (30일 보관 후 삭제)
```

> nginx `/cdn/` location은 `/var/lib/vaultix/assets/published/`에 alias. `/dl/` location은 X-Accel-Redirect로 동일 디렉토리 참조.

---

## 4. 코드/설정 골격 (Phase 0 산출물 위에 추가되는 것)

### 4.1 docker-compose 추가분 (Phase 1)

A3 §4.2를 그대로 옴김 + 아래 추가:

```yaml
  celery-beat:
    image: ghcr.io/${GH_OWNER}/vaultix-api:${IMAGE_TAG}
    container_name: vaultix-celery-beat
    restart: unless-stopped
    networks: [internal]
    depends_on: [redis]
    environment:
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      DATABASE_URL: postgresql+psycopg://${PG_USER}:${PG_PASSWORD}@postgres:5432/vaultix
      TZ: Asia/Seoul
    command: celery -A vaultix_api.workers.celery_app beat --schedule /tmp/celerybeat-schedule
```

### 4.2 nginx 추가 location (자산 CDN)

```nginx
# /etc/nginx/sites-available/vaultix.conf 안 server 블록에 추가
location /cdn/ {
    alias /var/lib/vaultix/assets/published/;
    expires 30d;
    add_header Cache-Control "public, immutable";
    access_log off;
    # 핫링크 차단 (Phase 2 강화)
    valid_referers none blocked vaultix.example.com *.vaultix.example.com;
    if ($invalid_referer) { return 403; }
}
```

### 4.3 Resend 메일 어댑터 (FastAPI)

```python
# apps/api/src/vaultix_api/adapters/resend_mail.py
import httpx
from vaultix_api.settings import settings


class MailError(Exception): pass


async def send_email(to: str, subject: str, html: str, *, reply_to: str | None = None):
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": "vaultix <noreply@vaultix.example.com>",
                "to": [to],
                "subject": subject,
                "html": html,
                **({"reply_to": [reply_to]} if reply_to else {}),
            },
        )
        if r.status_code >= 300:
            raise MailError(f"resend {r.status_code} {r.text[:200]}")
        return r.json()
```

### 4.4 Auth.js v5 골격 (apps/web)

```ts
// apps/web/src/auth.ts
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { DrizzleAdapter } from "@auth/drizzle-adapter";  // 또는 직접 어댑터 (PG raw)
// ... 또는 Prisma adapter 등 ORM 결정 후

export const { auth, handlers, signIn, signOut } = NextAuth({
  adapter: /* PG sessions 테이블 어댑터 */,
  session: { strategy: "database", maxAge: 30 * 24 * 60 * 60 },
  providers: [
    Credentials({
      credentials: { email: {}, password: {} },
      async authorize(creds) {
        const user = await fetch(`${process.env.API_BASE}/api/v1/auth/_login`, {
          method: "POST",
          body: JSON.stringify(creds),
          headers: { "Content-Type": "application/json" },
        }).then(r => r.ok ? r.json() : null);
        return user?.data?.user ?? null;
      },
    }),
  ],
  pages: {
    signIn: "/auth/login",
    verifyRequest: "/auth/verify-email",
  },
});
```

> Phase 2에서 Google/Kakao Provider 추가.

### 4.5 메타데이터 생성 프롬프트 (A7 LLM 라우터)

```python
# apps/api/src/vaultix_api/services/auto_metadata.py
from vaultix_api.services.llm_router import TaskType, call_llm_json


META_SYSTEM = """당신은 한국어 이미지 자산 메타데이터 작성 전문가입니다.
입력: 이미지의 영어 프롬프트
출력: JSON {title_ko, description_ko, alt_text_ko, tags_ko: [...]}
- title_ko: 30자 이내, 자연스러운 한국어
- description_ko: 80자 이내
- alt_text_ko: 시각장애인을 위한 묘사. 100자 이내
- tags_ko: 5개, 단어 1~3 음절
- JSON 외 텍스트 금지"""


async def generate_metadata(prompt: str) -> dict:
    return await call_llm_json(
        task=TaskType.METADATA_GEN,
        system=META_SYSTEM,
        user=prompt,
        timeout_s=30,
    )
```

### 4.6 환경변수 추가분 (.env)

```dotenv
# Phase 1
RESEND_API_KEY=
TURNSTILE_SECRET=
COMFY_HOST=http://100.x.x.x:8188
NANOBANANA_API_KEY=
NANOBANANA_BASE_URL=
OPENAI_API_KEY=
OPENAI_IMAGE_MODEL=gpt-image-2
ANTHROPIC_API_KEY=
GOOGLE_AI_API_KEY=
ZAI_API_KEY=
SIGNED_URL_SECRET=                 # HMAC 키, 64자 random
ASSET_ROOT=/data/assets
NEXT_PUBLIC_TURNSTILE_SITEKEY=
JH_ADMIN_EMAIL=naral3221@gmail.com
```

---

## 5. 테스트 계획

### 5.1 단위 테스트

| 영역 | 핵심 테스트 |
|------|------------|
| signed URL | HMAC 정합 / 만료 / nonce 1회용 |
| Rate limit | 30회 INCR / 31번째 429 / 1시간 후 reset |
| 다운로드 카운트 | UPSERT 동작 (2번째는 카운트 X) |
| 메타데이터 LLM | 잘못된 JSON 응답 fallback (null 처리) |
| 슬러그 생성 | 충돌 시 suffix 동작 |
| 이미지 검증 | 깨진 파일 reject |
| 이미지 점수 | CLIP 임베딩 결과 0~1 범위 |

### 5.2 통합 테스트 (Playwright E2E)

| 시나리오 | 검증 |
|---------|------|
| 박지원 페르소나 5분/5클릭 | 검색 → 자산상세 → 회원가입 → 인증 → 다운로드 |
| 김보미 페르소나 탐색 | 홈 → 컬렉션 → 무한스크롤 → ♡ 5개 → 즐겨찾기(Phase 2 검증 보류) |
| 한도 31번째 | 30회 정상 → 31번째 429 + Toast |
| 다크모드 | 토글 → localStorage 저장 → 새로고침 유지 |
| 어드민 키보드 100% | 인박스 50장 키보드만으로 처리 |
| 비로그인 다운로드 시도 | 모달 → 회원가입 진입 |

### 5.3 부하·성능 테스트

- `wrk -t4 -c50 -d60s https://vaultix.example.com/api/v1/assets` → 에러율 0%, p95 < 200ms
- 동시 다운로드 50개 → 모두 200, signed URL 충돌 없음

### 5.4 베타 시나리오 (W8)

베타 5명에게 다음 작업 부여 후 관찰:
1. 회원가입 → 첫 다운로드까지 (목표 5분)
2. 좋아하는 자산 5개 찾아서 다운로드 (목표 10분)
3. 한도 30회 도달 후 안내 확인
4. 모바일에서 동일 작업
5. 30분 인터뷰 (어떤 점이 좋았는지·불편했는지)

---

## 6. 리스크 & 대응

| 리스크 | 가능성 | 영향 | 대응 |
|--------|:---:|:---:|------|
| 데스크탑 ComfyUI 불안정 (Tailscale 끊김 잦음) | 中 | 高 | A3 §5 헬스 + 자동 fallback, JH가 데스크탑 켜는 시간대 명시 (23~02시 보장) |
| 외부 이미지 API 장애·도용 의심 | 中 | 高 | provider 헬스체크 + `/admin/panic` + 호출량 5배 이상 폭증 알림 |
| 메타데이터 LLM 한국어 품질 부족 | 中 | 中 | 인박스에서 30분 큐레이션이 보정. 큐레이션 부담 큰 항목은 LLM 프롬프트 개선 |
| 이미지 점수 모델(CLIP) 다운로드 큼 (~1.5GB) | 低 | 低 | Phase 0에서 미리 받음. 모델 캐시 볼륨 사용 |
| 베타 사용자 0명 (URL을 안 줌) | 中 | 中 | JH 본업 동료·대학동기 등 5명 명단 미리 확보 |
| 첫 다운로드 ZIP 버그 (한글 파일명) | 中 | 中 | RFC 5987 `filename*=UTF-8''...` 사용, 베타 전 검증 |
| Resend 무료 한도(월 3,000건) 초과 | 低 | 中 | 베타 단계는 충분. 발생 시 유료 전환($20/월) |
| 어드민 인박스 처리 못 따라감 | 中 | 中 | 자동 점수 임계 강화 (0.6+ 자동 승인 옵션 검토) |
| Auth.js v5 stable 미만 변경 | 低 | 中 | 5.0 정식 사용, breaking change 시 minor 버전 핀 |
| 데스크탑 GPU 작업·게임과 충돌 | 低 | 低 | Phase 1 일반 생성은 외부 API가 담당. ComfyUI는 특수 워크플로우용 헬스만 유지 |
| 큐레이션 인박스 키보드 단축키 OS 충돌 | 中 | 低 | 단축키 도움말(?)에 명시, 충돌 시 사용자 정의 가능 (Phase 2) |

---

## 6.5 v0.4 보강 작업 (99B + A7 반영)

> §2 WBS에 추가되는 작업 항목들. 기존 WBS는 그대로 두되, 각 그룹에 다음을 끼워넣는다.

### 6.5.1 새 WBS 항목

| ID | 그룹 | 작업 | 결정 ID |
|----|------|------|---------|
| W2.4 | DB | A1 §17 v0.4 보강 테이블 마이그레이션 (0013~0018) | T-10·T-11·T-12·B-09·B-13 |
| W3.6 | API | LLM 라우팅 레이어 `backend/llm_router.py` 구현 (A7 §3) | A7 D-13 |
| W3.7 | API | 외부 이미지 라우팅(`Nanobanana → gpt-image-2 → ComfyUI 특수`)으로 재구성 (A3 §6) | D-14·D-19 |
| W4.5 | UI | `/admin/panic` 응급 정지 페이지 + 백엔드 토글 | D-12 |
| W4.6 | UI | 어드민 대시보드 v0(read-only 5위젯) → v1(10위젯) | T-12 |
| W4.7 | UI | `/admin/takedowns` 신고 처리 화면 | B-09 |
| W4.8 | UI | `/admin/log/{date}` 일지 작성 페이지 + 인박스 ★ 토글 | B-13 |
| W6.4 | 이미지 | Nanobanana 어댑터 + OpenAI `gpt-image-2` 어댑터 | D-14·D-19 |
| W6.5 | 이미지 | EXIF 메타데이터 자동 주입 (생성 결과 파일에 AI 명시) | T-15 |
| W6.6 | 이미지 | HTML meta 태그 자동 생성 (`<meta name="ai-generated">`) | T-15 |
| W7.4 | 발행 | `/report` 페이지 + 백엔드 takedown_requests 처리 | B-09 |
| W7.5 | 발행 | `/today` `/log` 공개 페이지 (B-13) | B-13 |
| W7.6 | 발행 | Listmonk 뉴스레터 셋업 + `/newsletter` 페이지 | B-12 |
| W7.7 | 발행 | pgBackRest WAL 아카이빙 → R2 송출 (T-11) | T-11 |
| W7.8 | 발행 | 자산 SHA-256 체크섬 자동 계산 + 주 1회 검증 cron | T-11 |

### 6.5.2 폐기되는 v0.3 작업

| 폐기 작업 | 폐기 사유 |
|----------|----------|
| Ollama Qwen 2.5 7B 메타데이터 | D-13 — 외부 LLM API로 통일 |
| Replicate API 어댑터 | D-14 — Nanobanana/`gpt-image-2`로 대체 |
| fal.ai 2순위 폴백 검토 | D-14 — 동일 |
| EXTERNAL_BUDGET_USD_PER_MONTH 비용 캡 | T-10 — 무제한 키로 의미 없음 (호출량 추적만) |
| 시간대별 ComfyUI 풀가동 정책 (23:00~06:00 50장 배치) | A3 §13 — Phase 1엔 ComfyUI 미사용 |

### 6.5.3 환경변수 변경 (.env)

```dotenv
# 추가 (D-14, A7)
NANOBANANA_API_KEY=
NANOBANANA_BASE_URL=
OPENAI_API_KEY=                    # gpt-image-2 + LLM 라우팅 공용
OPENAI_IMAGE_MODEL=gpt-image-2
ANTHROPIC_API_KEY=
GOOGLE_AI_API_KEY=
ZAI_API_KEY=

# pgBackRest / R2 (T-11)
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_BACKUP=vaultix-backups

# 폐기 (참고)
# OLLAMA_BASE_URL — D-13으로 폐기
# REPLICATE_API_TOKEN — D-14로 폐기
# FAL_API_KEY — 폐기
# EXTERNAL_BUDGET_USD_PER_MONTH — 무의미
```

---

## 7. Phase 2 진입 조건

> 다음을 **모두** 만족해야 Phase 2 시작.

- [ ] §1.2 완료 조건 모든 체크박스 ✅
- [ ] 베타 5명 시나리오 완수율 100%, 평균 만족도 4/5 이상
- [ ] 일 자동 발행 50장+ × 7일 연속
- [ ] **(v0.4)** Nanobanana 비중 ≥ 80%, `gpt-image-2` 폴백 ≤ 20% (ComfyUI 비중 0% — Phase 1엔 특수 워크플로우 미도입)
- [ ] **(v0.4)** 외부 API 호출량 추적 + Telegram 50%·80%·100% 알림 작동
- [ ] **(v0.4)** `/admin/panic` 토글 동작 검증 + 해제 검증
- [ ] **(v0.4)** `/report` 신고 1건 시뮬레이션 처리 완료 (24시간 내 응답)
- [ ] **(v0.4)** pgBackRest WAL 송출 + 분기 1회 복구 리허설 통과
- [ ] **(v0.4)** Listmonk 뉴스레터 첫 발송 (베타 5명 대상)
- [ ] **(v0.4)** 자산 SHA-256 체크섬 검증 cron 통과 (손상 0건)
- [ ] Sentry 에러율 < 0.5%
- [ ] Uptime Kuma 7일 99%+
- [ ] B1 §15.2 Vaultix 최종 네이밍 기준 워드마크 점검 + 정식 도메인 등록 완료
- [ ] 약관·라이선스(§6 신고 절차 포함)·privacy·about·contact 페이지 모두 발행
- [ ] 묶음 4 (Phase 2~5) 작성 완료

---

## 8. 다음 액션 (이 문서 외)

1. JH가 본 문서 + B2 + A1 + A2 + A3 정독 → 의견 수렴 → 본 문서 갱신
2. Phase 0이 §1.2 완료 조건을 충족하면 W1부터 착수
3. 막히는 항목은 코워크에서 "Phase 1 §2.WX 항목 X.Y에서 막힘" 형식으로 질문


