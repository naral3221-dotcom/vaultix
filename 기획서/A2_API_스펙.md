# A2 — API 스펙 (FastAPI)

> **목적**: Phase 1~5에서 노출되는 모든 HTTP 엔드포인트를 정의. Phase 1 엔드포인트는 상세, 이후 Phase는 요약.
> **베이스 URL**: `https://vaultix.example.com/api`
> **버전**: `/api/v1/...` 으로 prefix. 호환성 깨질 변경 시 `/v2`로 점프.
> **인증**: 사용자 = Auth.js v5 세션 쿠키 (`__Secure-vaultix.session`). 어드민 = 같은 세션 + Tailscale IP + role 검증.
> **응답 포맷**: JSON. 시간 필드는 ISO 8601 UTC.

---

## 1. 공통 규칙

### 1.1 응답 포맷

**성공**:
```json
{
  "data": { ... },
  "meta": { ... }   // optional (페이지네이션, 통계 등)
}
```

**에러** (RFC 7807 Problem Details + 자체 확장):
```json
{
  "type": "https://vaultix.example.com/errors/rate-limit-exceeded",
  "title": "Rate limit exceeded",
  "status": 429,
  "detail": "시간당 30회 한도를 초과했어요. 38분 뒤에 다시 시도해 주세요.",
  "code": "rate_limit_exceeded",          // 클라이언트 분기용 stable key
  "context": { "retry_after_seconds": 2280 }
}
```

| 표준 코드 | 의미 |
|----------|------|
| `validation_error` | 폼/요청 스키마 위반 |
| `unauthenticated` | 로그인 필요 |
| `email_not_verified` | 이메일 인증 필요 |
| `forbidden` | 권한 부족 |
| `not_found` | 자원 없음 |
| `conflict` | 중복 / 상태 충돌 |
| `rate_limit_exceeded` | 한도 초과 |
| `payment_required` | (Phase 5+) 유료 한도 |
| `service_unavailable` | 외부 의존 실패 |
| `internal_error` | 서버 오류 |

### 1.2 페이지네이션

cursor 기반 (성능·중복 회피):
```
GET /api/v1/assets?cursor=eyJpZCI6MTIzfQ&limit=24
```

**응답 meta**:
```json
{
  "meta": {
    "next_cursor": "eyJpZCI6MTQ3fQ",
    "limit": 24,
    "total_estimate": 12500   // 정확치 X, 추정값
  }
}
```

> Cursor는 `{id, sort_value}` base64. 한 페이지 max 100. 검색 결과는 50까지.

### 1.3 Rate Limiting

| 영역 | 한도 |
|------|------|
| 비로그인 GET | IP당 60 req/min |
| 비로그인 POST (회원가입, 검색 등) | IP당 10 req/min |
| 로그인 GET | 사용자당 120 req/min |
| 로그인 다운로드 | 사용자당 30 req/hour (B-04) |
| 어드민 | 무제한 (단, audit log 기록) |

응답 헤더:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 47
X-RateLimit-Reset: 1714200000
```

429 응답 시 `Retry-After` 헤더 + `context.retry_after_seconds`.

### 1.4 헤더

| 요청 헤더 | 용도 |
|---------|------|
| `Accept-Language: ko,en;q=0.9` | i18n 컨텐츠 자동 선택 (Phase 2) |
| `X-Forwarded-For` | 시스템 nginx → API 전달 (실제 사용자 IP) |
| `X-Forwarded-Proto: https` | scheme 판별 |
| `X-Tailscale-User` | Tailscale Funnel/Connect 시 본인 식별 (어드민에서 사용) |

| 응답 헤더 | 용도 |
|---------|------|
| `Cache-Control` | 정적 자원·sitemap 등 |
| `X-Request-Id` | 트레이싱 (UUIDv4) |
| `Server-Timing: db;dur=12, redis;dur=2` | 디버깅 (개발환경만) |

### 1.5 인증 흐름 (Auth.js v5 + 백엔드 검증)

1. Next.js가 Auth.js v5로 세션 발행 → DB(`sessions` 테이블)에 저장
2. 모든 API 호출 시 nginx → FastAPI로 `Cookie: __Secure-vaultix.session=...` 전달
3. FastAPI는 미들웨어로 `sessions` 테이블 조회 → `request.state.user` 주입
4. Tailscale IP 체크는 nginx에서 `X-Real-IP` + role 체크는 FastAPI에서

### 1.6 어드민 권한

```python
# apps/api/src/vaultix_api/deps.py
from fastapi import Depends, HTTPException, Request

def require_user(req: Request):
    user = req.state.user
    if not user:
        raise HTTPException(401, "unauthenticated")
    return user

def require_verified(user = Depends(require_user)):
    if not user.email_verified_at:
        raise HTTPException(403, "email_not_verified")
    return user

def require_admin(user = Depends(require_user)):
    # Phase 1: 단순 이메일 매칭. Phase 4: roles 테이블
    if user.email_lower not in {"naral3221@gmail.com"}:  # JH
        raise HTTPException(403, "forbidden")
    # 추가: nginx에서 이미 Tailscale ALLOW 룰 통과한 상태여야 함
    return user
```

---

## 2. 헬스 / 메타

### 2.1 `GET /healthz`

```http
GET /healthz
```
**응답**:
```json
{ "status": "ok", "version": "1.0.42", "env": "production" }
```

### 2.2 `GET /api/v1/meta/categories`

분류 트리 전체. 5분 캐시.

```http
GET /api/v1/meta/categories?asset_type=image
```

```json
{
  "data": [
    {"id": 1, "slug": "business", "name_ko": "비즈니스", "name_en": "Business", "children": [
      {"id": 11, "slug": "business-meeting", "name_ko": "미팅"}
    ]},
    {"id": 2, "slug": "lifestyle", "name_ko": "라이프스타일"}
  ]
}
```

### 2.3 `GET /api/v1/meta/tags?q=...`

태그 자동완성. 시작하는 단어 매칭.

```http
GET /api/v1/meta/tags?q=비즈&limit=10
```

---

## 3. /auth (Phase 1)

### 3.1 `POST /api/v1/auth/signup`

```http
POST /api/v1/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "min8자리",
  "display_name": "박지원",
  "locale": "ko",
  "turnstile_token": "XXXXX"
}
```

**검증**:
- email RFC 5322
- password 8자+, ≥1 숫자
- turnstile_token 검증 (Cloudflare Turnstile)
- 일회용 메일 도메인 차단 (목록 관리)

**응답** (201):
```json
{
  "data": {
    "user": { "id": 123, "email": "user@example.com", "email_verified": false }
  }
}
```

이후 자동으로 인증 메일 발송 (Resend).

### 3.2 `POST /api/v1/auth/login`

> Auth.js v5가 처리. FastAPI는 호출되지 않음. 단, FastAPI 측에서 `last_login_at` 업데이트 후크는 webhook으로 받음.

### 3.3 `POST /api/v1/auth/verify-email`

```json
{ "token": "eyJ...48-bytes-urlsafe" }
```

**응답**:
```json
{ "data": { "verified": true, "user_id": 123 } }
```

만료/사용된 토큰: 410 Gone, `code: "verification_token_invalid"`.

### 3.4 `POST /api/v1/auth/resend-verification`

로그인+미인증 사용자만. 5분 쿨다운.

### 3.5 `POST /api/v1/auth/forgot-password`

```json
{ "email": "user@example.com" }
```

응답은 항상 200 (이메일 존재 여부 미노출).

### 3.6 `POST /api/v1/auth/reset-password`

```json
{ "token": "...", "new_password": "..." }
```

### 3.7 `POST /api/v1/auth/logout`

세션 무효화. Auth.js와 협력.

---

## 4. /me

### 4.1 `GET /api/v1/me`

```json
{
  "data": {
    "id": 123,
    "email": "user@example.com",
    "display_name": "박지원",
    "locale": "ko",
    "email_verified": true,
    "stats": {
      "downloads_count": 42,
      "favorites_count": 8,
      "downloads_remaining_this_hour": 24
    }
  }
}
```

### 4.2 `PATCH /api/v1/me`

```json
{ "display_name": "...", "locale": "ko" }
```

### 4.3 `DELETE /api/v1/me`

소프트 삭제 (`status='deleted'`). Resend·DB·assets 영향 없음. 30일 후 hard delete.

---

## 5. /assets (Phase 1 — 이미지)

### 5.1 `GET /api/v1/assets` — 탐색·정렬·필터

```http
GET /api/v1/assets
  ?type=image
  &category=business
  &tag=meeting,office
  &orientation=landscape|portrait|square
  &color=blue                       (Phase 2)
  &sort=popular|recent|trending
  &cursor=...
  &limit=24
```

**응답**:
```json
{
  "data": [
    {
      "id": 12345,
      "slug": "business-meeting-illustration-modern",
      "asset_type": "image",
      "title": "비즈니스 미팅 일러스트",
      "alt_text": "테이블에 둘러앉은 사람들이 회의하는 모습",
      "thumbnail_url": "https://vaultix.example.com/cdn/thumb/12345.webp",
      "preview_url":   "https://vaultix.example.com/cdn/preview/12345.webp",
      "width": 1024, "height": 1024, "aspect_ratio": "1:1",
      "category": { "id": 1, "slug": "business", "name": "비즈니스" },
      "tags": [{"slug":"meeting","name":"미팅"}],
      "ai": { "model": "flux-dev", "generator": "comfy" },
      "stats": { "downloads": 1234, "favorites": 87 },
      "published_at": "2026-04-30T08:00:00Z"
    }
  ],
  "meta": { "next_cursor": "...", "limit": 24, "total_estimate": 12500 }
}
```

### 5.2 `GET /api/v1/assets/{slug_or_id}` — 상세

slug 우선, 숫자 path는 id 처리.

```json
{
  "data": {
    "id": 12345,
    "slug": "...",
    "title": "...",
    "description": "...",
    "alt_text": "...",
    "asset_type": "image",
    "category": { ... },
    "tags": [ ... ],
    "files": [
      {"variant":"original","format":"png","width":1024,"height":1024,"size_bytes":2_345_678},
      {"variant":"webp","format":"webp","width":1024,"height":1024,"size_bytes":345_678}
    ],
    "preview_url": "...",
    "ai": { "model": "flux-dev", "generator": "comfy", "params": { ... } },
    "license_summary_url": "/license#summary",
    "stats": { "downloads": 1234, "favorites": 87, "views": 9876 },
    "related_asset_ids": [98, 99, 100],
    "published_at": "..."
  }
}
```

### 5.3 `GET /api/v1/assets/{id}/related` — "이 스타일 더 보기"

같은 카테고리 + 임베딩 유사도 (Phase 2 임베딩 도입 전엔 카테고리+태그 매칭).

### 5.4 `POST /api/v1/assets/{id}/view` — 조회수 증가

비동기. 5초 throttle 동일 user/asset 1회.

### 5.5 `GET /api/v1/search`

```http
GET /api/v1/search?q=비즈니스&type=image&limit=24
```

PG `to_tsvector`. Phase 2 OpenSearch/Meilisearch 검토.

---

## 6. /downloads (가장 중요)

### 6.1 `POST /api/v1/downloads/{asset_id}` — signed URL 발급

**전제**:
- 로그인 + 이메일 인증 (`require_verified`)
- 해당 시간(`HH`) 다운로드 카운트 < 30
- asset.status='published'

**응답** (200):
```json
{
  "data": {
    "url": "https://vaultix.example.com/dl/12345/abc123nonce?exp=1714200000&sig=...",
    "expires_at": "2026-04-30T08:05:00Z",
    "filename": "business-meeting-illustration-modern.png",
    "size_bytes": 2_345_678,
    "asset": { "id": 12345, "slug": "..." }
  }
}
```

**에러**:
- 401 `unauthenticated`
- 403 `email_not_verified`
- 404 `not_found`
- 429 `rate_limit_exceeded` + `context.retry_after_seconds`

**처리 순서** (서버):
1. 권한 체크
2. Redis `dl:{user_id}:{YYYYMMDDHH}` INCR + TTL 3600
3. INCR 결과 > 30이면 DECR 롤백 + 429
4. signed URL 생성 (HMAC-SHA256, 만료 5분, nonce 1회용)
5. Redis `dl:nonce:{nonce}` SETEX 300s
6. URL 반환

### 6.2 `GET /dl/{asset_id}/{nonce}` — 실제 파일 전송

> 별도 라우터. JSON 응답 X. nginx `X-Accel-Redirect`로 정적 파일 전송.

```python
@router.get("/dl/{asset_id}/{nonce}")
async def download_file(asset_id: int, nonce: str, exp: int, sig: str, request: Request, db = Depends(get_db)):
    # 1. nonce 검증·소비 (Redis GETDEL)
    # 2. 만료 검증 (exp > now)
    # 3. 시그니처 검증
    # 4. asset 조회
    # 5. downloads 테이블 UPSERT (B-04 정책)
    #    - 새 row 또는 (user_id, asset_id) 갱신
    # 6. asset.download_count 증가 (atomic)
    # 7. 응답: X-Accel-Redirect로 nginx에 위임
    return Response(headers={
        "X-Accel-Redirect": f"/assets/raw/{asset.file_path}",
        "Content-Disposition": f'attachment; filename="{filename}"',
    })
```

> **카운트 규칙**: `B-04` — `bytes_sent > 0` & 응답 200 시점에 카운트. 동일 user/asset 재요청은 카운트 X (UPSERT만).

### 6.3 `GET /api/v1/me/downloads` — 다운로드 내역

```http
GET /api/v1/me/downloads?cursor=...&limit=20
```

```json
{
  "data": [
    { "asset": { ... }, "downloaded_at": "...", "bytes_sent": 2345678 }
  ],
  "meta": { "next_cursor": "..." }
}
```

---

## 7. /favorites (Phase 2)

### 7.1 `POST /api/v1/favorites/{asset_id}` / `DELETE`

Idempotent. 200 OK + `{"data":{"favorited":true,"favorite_count":88}}`.

### 7.2 `GET /api/v1/me/favorites`

페이지네이션.

---

## 8. /admin (Phase 1)

> 모두 `require_admin` + nginx의 Tailscale ALLOW 통과 필요.

### 8.1 큐레이션 인박스

#### `GET /api/v1/admin/inbox`

```http
GET /api/v1/admin/inbox
  ?asset_type=image
  &min_score=0.4
  &category=business
  &limit=20
```

**응답** (큐 패턴):
```json
{
  "data": [
    {
      "asset_id": 99001,
      "asset_type": "image",
      "preview_url": "...",
      "auto_metadata": {
        "title_ko": "비즈니스 미팅 일러스트",
        "description_ko": "...",
        "alt_text_ko": "...",
        "tags_suggested": ["meeting","business"]
      },
      "category_suggested": { "id": 1, "slug": "business" },
      "quality_score": 0.82,
      "ai": {"model":"flux-dev","generator":"comfy"},
      "prompt_text": "business meeting illustration, ...",
      "generation_job_id": 88001,
      "created_at": "..."
    }
  ],
  "meta": { "remaining_in_inbox": 47, "today_processed": 23 }
}
```

#### `POST /api/v1/admin/inbox/{asset_id}/approve`

```json
{
  "title_ko": "...",       // 옵션 (자동 생성된 값 수정 시)
  "description_ko": "...",
  "alt_text_ko": "...",
  "category_id": 1,
  "tags": ["meeting","business"]
}
```

서버 처리:
1. asset.status = 'approved' → 즉시 발행 큐로 enqueue (시간 분산)
2. asset.title_ko 등 수정값 반영
3. asset_tags 동기화
4. admin_audit_logs 기록
5. 다음 인박스 카드 응답에 포함 가능 (옵션)

응답:
```json
{
  "data": { "asset_id": 99001, "status": "approved", "next": { ...next card... } }
}
```

#### `POST /api/v1/admin/inbox/{asset_id}/reject`

```json
{ "reason": "low_quality" }
```

- asset.status = 'rejected'
- 결과 PNG는 보존 (학습/디버깅용)
- prompt_template.performance_score에 반영 (rejection_rate↑)

#### `POST /api/v1/admin/inbox/{asset_id}/hold`

asset.status = 'inbox' 유지 + 별도 hold flag (re-review 표시).

#### `POST /api/v1/admin/inbox/{asset_id}/regenerate`

같은 prompt_template로 새 generation_job 생성 (다른 seed).

### 8.2 자산 관리

| 메소드 / 경로 | 용도 |
|--------------|------|
| `GET /api/v1/admin/assets` | 모든 상태 자산 검색 (status 필터 포함) |
| `GET /api/v1/admin/assets/{id}` | 상세 (audit 포함) |
| `PATCH /api/v1/admin/assets/{id}` | 메타 수정 |
| `POST /api/v1/admin/assets/{id}/archive` | 발행 자산 숨김 |
| `POST /api/v1/admin/assets/{id}/republish` | 복구 |

### 8.3 프롬프트 풀 관리

| 메소드 / 경로 | 용도 |
|--------------|------|
| `GET /api/v1/admin/prompt-templates` | 목록 |
| `POST /api/v1/admin/prompt-templates` | 생성 |
| `PATCH /api/v1/admin/prompt-templates/{id}` | 가중치/활성화/내용 |
| `DELETE /api/v1/admin/prompt-templates/{id}` | 삭제 |
| `POST /api/v1/admin/prompt-templates/{id}/run-once` | 즉시 1장 생성 시도 (테스트용) |

### 8.4 생성 작업 / 큐 모니터

| 메소드 / 경로 | 용도 |
|--------------|------|
| `GET /api/v1/admin/jobs` | 작업 목록 (status 필터) |
| `GET /api/v1/admin/jobs/{id}` | 작업 상세 (raw_path, error 등) |
| `POST /api/v1/admin/jobs/{id}/retry` | 재시도 |
| `GET /api/v1/admin/queue/status` | A3 §7.3 응답 |

### 8.5 사용자

| 메소드 / 경로 | 용도 |
|--------------|------|
| `GET /api/v1/admin/users` | 검색 (email, status) |
| `POST /api/v1/admin/users/{id}/suspend` | 정지 |
| `POST /api/v1/admin/users/{id}/reactivate` | 복구 |
| `GET /api/v1/admin/users/{id}/downloads` | 사용자별 다운로드 내역 |

### 8.6 어드민 감사 로그

| 메소드 / 경로 | 용도 |
|--------------|------|
| `GET /api/v1/admin/audit` | 전체 (시간 역순) |
| `GET /api/v1/admin/audit?target_type=asset&target_id=99001` | 특정 자산 변경 이력 |

### 8.7 일괄 액션

| 메소드 / 경로 | 용도 |
|--------------|------|
| `POST /api/v1/admin/inbox/batch-approve` | `{"asset_ids":[...]}` 일괄 승인 |
| `POST /api/v1/admin/inbox/batch-reject` | 일괄 폐기 |

---

## 9. 컬렉션 / 즐겨찾기 (Phase 2)

| 메소드 / 경로 | 용도 |
|--------------|------|
| `GET /api/v1/collections` | 공개 컬렉션 목록 |
| `GET /api/v1/collections/{slug}` | 상세 (assets 포함) |
| `POST /api/v1/admin/collections` | 생성 (admin) |
| `PATCH /api/v1/admin/collections/{id}` | 수정 |
| `POST /api/v1/admin/collections/{id}/items` | 자산 추가/제거 |

---

## 10. 메타 콘텐츠 / 블로그 (Phase 3)

### 10.1 공개

| 메소드 / 경로 | 용도 |
|--------------|------|
| `GET /api/v1/blog/posts` | 목록 (category, tag 필터) |
| `GET /api/v1/blog/posts/{slug}` | 상세 (locale별) |
| `GET /api/v1/blog/categories` | 카테고리 목록 |
| `POST /api/v1/blog/posts/{slug}/view` | 조회수 |
| `GET /api/v1/prompts/library` | 프롬프트 라이브러리 |
| `GET /api/v1/prompts/library/{slug}` | 상세 |
| `POST /api/v1/prompts/library/{slug}/copy` | 복사 카운트 (anonymous OK) |
| `GET /api/v1/tools` | AI 도구 디렉토리 |
| `GET /api/v1/tools/{slug}` | 상세 |
| `POST /api/v1/newsletter/subscribe` | 뉴스레터 구독 |
| `POST /api/v1/newsletter/confirm` | 더블 옵트인 확인 |
| `POST /api/v1/newsletter/unsubscribe` | 해제 |

### 10.2 어드민

| 메소드 / 경로 | 용도 |
|--------------|------|
| `GET /api/v1/admin/topics` | 토픽 후보 큐 |
| `POST /api/v1/admin/topics/{id}/approve` | 토픽 승인 → 초안 생성 트리거 |
| `POST /api/v1/admin/topics/{id}/reject` | 폐기 |
| `GET /api/v1/admin/blog/posts` | 모든 상태 |
| `POST /api/v1/admin/blog/posts` | 새 글 (수동) |
| `PATCH /api/v1/admin/blog/posts/{id}` | 편집 (draft → review → published) |
| `POST /api/v1/admin/blog/posts/{id}/publish` | 발행 + 다국어 자동 번역 큐잉 |
| `POST /api/v1/admin/blog/posts/{id}/regenerate-draft` | LLM 초안 재생성 |

---

## 11. Tier 2 컨텐츠 (Phase 4) — 엔드포인트 같음 (asset_type만 추가)

```http
GET /api/v1/assets?type=pptx
GET /api/v1/assets?type=svg
GET /api/v1/assets?type=docx
GET /api/v1/assets?type=xlsx
GET /api/v1/assets?type=html
GET /api/v1/assets?type=lottie
GET /api/v1/assets?type=colorbook
GET /api/v1/assets?type=icon_set
```

다운로드 흐름 동일. 어드민 인박스에서 type별 워크플로우 미리보기 다르게 표시.

---

## 12. A/B 테스트 (Phase 4)

| 메소드 / 경로 | 용도 |
|--------------|------|
| `GET /api/v1/ab/{key}` | 사용자에게 배정된 variant 응답 (자동 배정 포함) |
| `POST /api/v1/ab/{key}/track` | 이벤트 트래킹 (`{"event":"download"}`) |

어드민:
| 메소드 / 경로 | 용도 |
|--------------|------|
| `POST /api/v1/admin/ab` | 실험 생성 |
| `POST /api/v1/admin/ab/{id}/start` | 시작 |
| `POST /api/v1/admin/ab/{id}/end` | 종료 |
| `GET /api/v1/admin/ab/{id}/result` | 결과 |

---

## 13. 웹훅 / 외부 콜백

| 메소드 / 경로 | 출처 | 용도 |
|--------------|-----|------|
| `POST /api/v1/webhooks/resend/bounce` | Resend | 바운스 이메일 처리 |
| `POST /api/v1/webhooks/resend/complaint` | Resend | 스팸 신고 |
| `POST /api/v1/webhooks/listmonk/sync` | Listmonk (Phase 3) | 구독자 동기화 |
| `POST /api/v1/webhooks/turnstile/audit` | Cloudflare | 봇 의심 로그 |

웹훅은 HMAC 서명 검증 필수.

---

## 14. OpenAPI / 문서

- FastAPI 자동 OpenAPI: `/openapi.json`
- Swagger UI: `/docs` — production은 인증 필요
- 본 문서와 자동 생성 OpenAPI는 분기 1회 일치 검증 (CI에서 diff 알림)

---

## 15. 컨트랙트 테스트 (Phase 1 W7)

```python
# apps/api/tests/contract/test_downloads.py
def test_download_flow(client, user_verified, asset_published):
    r = client.post(f"/api/v1/downloads/{asset_published.id}")
    assert r.status_code == 200
    body = r.json()["data"]
    assert "url" in body
    assert body["expires_at"] > now()
    # 두 번째 요청은 같은 카운트 (B-04)
    r2 = client.post(f"/api/v1/downloads/{asset_published.id}")
    assert r2.status_code == 200
    # downloads 테이블에 row 1개만 있어야 함
```

전 엔드포인트 200·400·401·403·404·429 케이스 다 작성 (Phase 1 완료 조건).

---

## 16. 응답 시간 목표 (Phase 1)

| 엔드포인트 | p95 |
|-----------|-----|
| `GET /api/v1/assets` (필터·정렬) | < 150ms |
| `GET /api/v1/assets/{slug}` | < 80ms |
| `POST /api/v1/downloads/{id}` | < 100ms |
| `GET /dl/...` (실제 파일) | nginx X-Accel-Redirect라 거의 0ms 오버헤드 |
| 어드민 인박스 | < 200ms |
| 검색 | < 300ms (PG FTS) |

---

## 17. v0.4 신규 엔드포인트 (99B + A7 반영)

> **목적**: T-10·T-12·B-09·B-10·B-13·D-12 결정 + A7 LLM 라우팅에서 추가된 엔드포인트를 정의.

### 17.1 `POST /api/v1/report` — 신고 접수 (B-09)

비로그인도 가능. Turnstile 검증 필수.

**요청**:
```json
{
  "reporter_name": "홍길동",
  "reporter_email": "report@example.com",
  "reporter_phone": "+82-10-...",
  "asset_url": "https://vaultix.com/assets/professional-businesswoman-xyz",
  "report_type": "copyright",
  "evidence_file_token": "upload_xyz123",
  "statement": "이 자산은 제 작품과 매우 유사합니다 ...",
  "honest_filing": true,
  "turnstile_token": "..."
}
```

`evidence_file_token`은 사전에 `POST /api/v1/uploads/evidence`로 업로드된 파일의 토큰 (5MB 한도, PDF/이미지).

**응답 200**:
```json
{
  "data": {
    "ticket_number": "TD-2026-000001",
    "status": "received",
    "expected_response_within_hours": 24,
    "next_steps_message_ko": "접수 확인 메일을 보내드렸습니다. 영업일 기준 3일 내 검토 결과를 알려드립니다."
  }
}
```

부수 효과:
- `takedown_requests` row 생성 + JH Telegram 즉시 알림
- 신고자에게 접수 확인 이메일(Resend) 자동 발송
- `report_type='copyright'` + `evidence_file_token` 있으면 자동으로 자산 임시 비공개 (추후 검토)

### 17.2 어드민 — 신고 처리 (B-09)

| 메소드 / 경로 | 용도 |
|--------------|------|
| `GET /api/v1/admin/takedowns?status=received&limit=20` | 신고 목록 |
| `GET /api/v1/admin/takedowns/{id}` | 신고 상세 (증빙 파일 미리보기 포함) |
| `POST /api/v1/admin/takedowns/{id}/decide` | 처리 결정 |

**처리 요청 예시**:
```json
{
  "decision": "accepted",                    // 'accepted'|'rejected'|'additional_info_requested'
  "resolution_note": "명백한 침해로 확인되어 비공개 처리합니다.",
  "block_recipe": true,                       // true면 blocked_recipes 자동 등록
  "block_seed": false,
  "notify_reporter": true
}
```

**부수 효과** (decision='accepted' + block_recipe=true):
- 자산 status → 'taken_down', URL 410 Gone
- `blocked_recipes`에 prompt + model 조합 등록
- `admin_audit_logs` 기록
- 신고자에게 결과 메일 (notify_reporter=true)

### 17.3 `POST /api/v1/admin/panic` — 응급 정지 (D-12)

Tailscale + 어드민 권한 필수.

**요청**:
```json
{
  "action": "engage",                          // 'engage'|'release'
  "scope": ["external_api","queues","signups"],// 정지할 영역. 'all'이면 전부
  "reason": "도용 의심 / 비용 폭증 등 사유 메모"
}
```

**응답**:
```json
{
  "data": {
    "panic_active": true,
    "engaged_at": "2026-04-27T12:00:00Z",
    "scope": ["external_api","queues","signups"],
    "engaged_by": "JH"
  }
}
```

**부수 효과**:
- Redis 플래그 `panic:engaged` 설정
- Celery 큐 일시 정지 (worker_revoke 신호)
- 외부 API 라우팅 비활성 (모든 호출 503 반환)
- 신규 가입 차단 (404 또는 안내 페이지)
- 기존 사용자 다운로드는 유지

`GET /api/v1/admin/panic/status`로 현재 상태 확인.

### 17.4 `GET /api/v1/today` — 오늘의 큐레이션 (B-13)

비로그인 가능.

**요청**: `GET /api/v1/today?date=2026-04-27` (date 생략 시 오늘)

**응답 200**:
```json
{
  "data": {
    "log_date": "2026-04-27",
    "assets": [
      {
        "id": 1234,
        "slug": "professional-...",
        "title_ko": "...",
        "thumbnail_path": "...",
        "jh_comment": "이번 주 최고. 자료에 바로 쓸 수 있어요."
      }
    ],
    "stats": {
      "assets_published": 47,
      "downloads_total": 312,
      "new_signups": 8
    },
    "previous_date": "2026-04-26",
    "next_date": null   // 미래는 null, 과거 페이지에선 다음 날짜
  }
}
```

캐시 30분, ETag 사용.

### 17.5 `GET /api/v1/log` — 운영 일지 (B-13)

**요청**: `GET /api/v1/log?cursor=...&limit=10` (날짜 역순 페이지네이션)

**응답 200**:
```json
{
  "data": [
    {
      "log_date": "2026-04-27",
      "stats": {
        "assets_published": 47,
        "downloads_total": 312,
        "new_signups": 8,
        "blog_posts_published": 1
      },
      "jh_note": "오늘은 미니멀 PPT 발행이 잘됨. K-스타일 LoRA 시도 결과 50% 만족.",
      "experiments_tried": [
        {"name": "consistent_character.json v2", "result": "fail", "note": "캐릭터 얼굴 변형이 심함"}
      ],
      "curated_count": 8
    }
  ],
  "meta": { "next_cursor": "..." }
}
```

비공개(`is_published=false`) 항목은 어드민에만 노출.

### 17.6 어드민 — 일지 작성 (B-13)

| 메소드 / 경로 | 용도 |
|--------------|------|
| `GET /api/v1/admin/log/{date}` | 특정 날짜 일지 조회/편집용 |
| `PATCH /api/v1/admin/log/{date}` | jh_note, experiments_tried, is_published 수정 |
| `POST /api/v1/admin/log/{date}/curate` | 자산 ★ 토글 (curated_asset_ids 갱신) |

### 17.7 `POST /api/v1/account/delete-account` — GDPR 삭제권 (B-10)

로그인 필수.

**요청**:
```json
{
  "confirmation_email": "user@example.com",   // 본인 확인용
  "reason": "no_longer_needed",                // 선택, 통계용
  "feedback": "..."                             // 선택
}
```

**응답 200**:
```json
{
  "data": {
    "scheduled_deletion_at": "2026-05-27T...",  // 30일 grace period
    "cancellation_url": "https://vaultix.com/account/cancel-deletion?token=..."
  }
}
```

30일간은 cancel 가능. 30일 후 익명화 cron이 실행:
- users.email/password_hash/display_name → NULL
- users.status → 'deleted'
- downloads.user_id 유지(통계용), 단 PII 분리
- favorites/sessions 전부 삭제

### 17.8 `GET /api/v1/account/export-data` — GDPR 데이터 이동권 (B-10)

로그인 필수.

**요청**: `GET /api/v1/account/export-data?format=zip`

**응답**:
- 200 + `Content-Type: application/zip`
- ZIP 내용:
  - `account.json` — 가입 정보, 동의 이력
  - `downloads.json` — 다운로드 이력
  - `favorites.json` — 즐겨찾기
  - `oauth_links.json` — 연결된 OAuth 계정
  - `README.txt` — 데이터 설명 + GDPR 권리 안내
- 생성에 30초 이상 걸리면 비동기 모드 (job_id 반환 후 완료 시 메일로 다운로드 링크)

Rate limit: 사용자당 7일 1회.

### 17.9 어드민 대시보드 (T-12) — 위젯 데이터

| 메소드 / 경로 | 용도 |
|--------------|------|
| `GET /api/v1/admin/dashboard/today` | 오늘의 운영 지표 (좌측 컬럼 1~5) |
| `GET /api/v1/admin/dashboard/traffic` | 트래픽·매출 (중앙 컬럼 6~10) |
| `GET /api/v1/admin/dashboard/system` | 시스템 상태 (우측 컬럼 11~15) |
| `GET /api/v1/admin/dashboard/assets/top?period=24h&limit=10` | Top/Worst 자산 |

**예시 응답** (`/today`):
```json
{
  "data": {
    "published_today": 47,
    "target_today": 50,
    "inbox_pending": 23,
    "queue_status": {
      "image_primary": 5,
      "image_secondary": 0,
      "image_special": 2,
      "image_post": 8
    },
    "external_api_calls_today": {
      "nanobanana": 47,
      "gpt_image_2": 3,
      "anthropic": 12,
      "openai": 5,
      "google_ai": 22,
      "zai": 47
    },
    "error_rate_24h": 0.003,
    "error_rate_prev_24h": 0.005
  }
}
```

### 17.10 어드민 — 특수 워크플로우 트리거 (D-14, A3 §3.2)

| 메소드 / 경로 | 용도 |
|--------------|------|
| `POST /api/v1/admin/special/series` | 같은 캐릭터 시리즈 N장 |
| `POST /api/v1/admin/special/pose` | ControlNet 포즈 변형 |
| `POST /api/v1/admin/special/style-lora` | 한국 일러스트 LoRA |
| `POST /api/v1/admin/special/inpaint` | 부분 인페인팅 |

**시리즈 트리거 예시**:
```json
{
  "parent_asset_id": 1234,
  "count": 12,
  "seed_strategy": "consistent",   // 같은 시드 + 변형 프롬프트
  "scenes": [
    {"prompt_suffix": "presenting confidently"},
    {"prompt_suffix": "taking a phone call"}
  ]
}
```

**응답**:
```json
{
  "data": {
    "queued_jobs": [5001, 5002, ...],
    "estimated_completion": "depends on desktop availability",
    "comfy_health": "up"
  }
}
```

### 17.11 LLM 라우팅 관찰성 (A7 §3.2)

| 메소드 / 경로 | 용도 |
|--------------|------|
| `GET /api/v1/admin/llm/calls?task=blog_draft&limit=50` | 최근 호출 로그 |
| `GET /api/v1/admin/llm/stats?period=today` | 모델별 호출 수·실패율·평균 지연 |
| `GET /api/v1/admin/llm/cost?period=this_month` | 호출량 추정 비용 (참고용) |

### 17.12 자산 레시피 (B-11) — 공개 조회 + 다운로드

| 메소드 / 경로 | 용도 |
|--------------|------|
| `GET /api/v1/assets/{slug}/recipe` | 레시피 메타 (모델·프롬프트·시드·CFG 등) |
| `GET /api/v1/assets/{slug}/recipe/workflow.json` | ComfyUI 워크플로우 JSON 다운로드 (특수 워크플로우만) |

**레시피 응답 예시**:
```json
{
  "data": {
    "model_name": "nanobanana-v3",
    "generator": "nanobanana",
    "prompt_positive": "professional businesswoman in modern office, soft natural light, ...",
    "prompt_negative": "low quality, blurry",
    "seed": 1234567890,
    "cfg_scale": 3.5,
    "steps": 28,
    "license": "CC0",
    "has_workflow_json": false,    // ComfyUI 특수 워크플로우인 경우만 true
    "stats": {
      "view_count": 234,
      "copy_count": 47,
      "workflow_download_count": 0
    }
  }
}
```

`GET ./workflow.json`은 ComfyUI 특수 워크플로우 자산만 200, 그 외 404.

부수: 응답마다 `view_count`, `copy_count`(쿼리 `?action=copy`), `workflow_download_count`(workflow.json 다운로드) INCR.

### 17.13 자산↔블로그 자동 추천 (T-14, Phase 3)

| 메소드 / 경로 | 용도 |
|--------------|------|
| `GET /api/v1/assets/{slug}/related?kind=blogs&limit=3` | 임베딩 유사도 기반 관련 블로그 |
| `GET /api/v1/assets/{slug}/related?kind=assets&limit=12` | 같은 카테고리 + 임베딩 유사 자산 |
| `GET /api/v1/blog/{slug}/related-assets?limit=12` | 블로그 페이지의 자산 그리드 |

내부적으로 `pgvector` 코사인 유사도 + `assets.status='published'` 필터.

### 17.14 모바일 PWA 큐레이션 (T-12, D-12)

`GET /api/v1/admin/inbox/mobile?limit=20`

기존 `/admin/inbox`와 응답 구조 같지만:
- 한 응답에 자산 1개만 (스와이프 단위)
- 큰 미리보기 URL (모바일 풀스크린용 1024px)
- 결정 액션: `POST /api/v1/admin/inbox/{id}/decision` (mobile 큐는 같은 엔드포인트 사용)

오프라인 큐잉: 클라이언트가 IndexedDB에 결정 저장 → 통신 복구 시 `POST /api/v1/admin/inbox/sync-decisions` (배치).

---

## 18. 다음 문서로 이어지는 결정

- 이 스펙의 모든 엔드포인트는 02 Phase 1 §WBS의 W2(api-assets), W3(api-downloads), W4(admin) 등 작업 항목에 1:1 대응.
- /admin/inbox의 응답 구조 → B2 §4.4 큐레이션 인박스 와이어와 정확 매칭.
- 다국어 응답 (Phase 2)은 응답 본문에 `Accept-Language` 헤더 기반 `title/description/alt_text` 자동 선택. `?locale=` 쿼리도 허용.
- **(v0.4)** 신규 엔드포인트들은 02·03·04 Phase의 새 WBS 항목에 매핑됨 — 02_Phase1 §갱신, 03_Phase2 §갱신, 04_Phase3 §갱신 참조.
- **(v0.4)** `/report`, `/today`, `/log`, `/account/delete-account`, `/account/export-data`, `/admin/panic` 페이지 와이어프레임은 B2 §갱신 참조.

