# A1 — 데이터 모델 & DDL

> **목적**: Phase 1~5에서 사용하는 모든 데이터베이스 스키마를 한 문서에 통합. Phase별로 어느 시점에 추가/변경되는지 명시.
> **DBMS**: PostgreSQL 17
> **마이그레이션 도구**: Alembic 1.13+
> **명명 규칙**: snake_case 테이블·컬럼, PK는 `id` (BIGSERIAL), FK는 `<table>_id`, 시간 컬럼은 `created_at` / `updated_at` / `published_at` 등 `_at` 접미.
> **타임존**: 모든 timestamp는 `TIMESTAMPTZ`. 앱 측은 항상 UTC로 저장, 표시 시 KST로 변환.

---

## 1. 마이그레이션 순서 (Alembic 리비전)

| Rev | 파일명 | Phase | 내용 |
|----|--------|:---:|------|
| 0001 | `0001_init_users_assets.py` | 1 | users, email_verifications, sessions, categories, tags, asset_tags, assets, asset_files |
| 0002 | `0002_downloads.py` | 1 | downloads, download_rate_limits (또는 Redis 운용 시 X) |
| 0003 | `0003_prompt_templates.py` | 1 | prompt_templates, generation_jobs |
| 0004 | `0004_admin_audit.py` | 1 | admin_audit_logs |
| 0005 | `0005_unified_assets.py` | 2 | assets에 type별 컬럼 추가, asset_translations, content_type 확장 |
| 0006 | `0006_oauth_favorites.py` | 2 | oauth_accounts, favorites |
| 0007 | `0007_collections.py` | 2 | collections, collection_items |
| 0008 | `0008_blog.py` | 3 | blog_posts, blog_post_translations, topics, topic_sources |
| 0009 | `0009_newsletter.py` | 3 | newsletter_subscribers (Listmonk 연동 후 미러) |
| 0010 | `0010_prompts_library.py` | 3 | prompt_library_items (사용자 노출용 프롬프트 라이브러리, 풀과 별도) |
| 0011 | `0011_tools_directory.py` | 3 | tools (AI 도구 디렉토리), tool_categories, tool_reviews |
| 0012 | `0012_ab_tests.py` | 4 | ab_experiments, ab_assignments |
| **0013** | `0013_v04_cost_llm_log.py` | **0** | cost_meter, llm_call_log (T-10, A7 D-13) |
| **0014** | `0014_v04_assets_v4_columns.py` | **0** | assets.checksum, assets.first_download_at, assets.embedding(VECTOR), assets.status에 'taken_down' 추가 |
| **0015** | `0015_v04_generation_jobs_v4.py` | **0** | generation_jobs: status enum 확장(`queued_special`, `generating_special`), generator enum 변경(replicate/fal 제거 → nanobanana/gpt_image_2/comfyui), workflow_template/workflow_params/parent_asset_id 컬럼 추가 (D-14) |
| **0016** | `0016_v04_asset_metrics.py` | **0** | asset_metrics_daily (T-12) |
| **0017** | `0017_v04_takedown.py` | **1** | takedown_requests, blocked_recipes (B-09) |
| **0018** | `0018_v04_daily_logs.py` | **1** | daily_logs (B-13) |
| **0019** | `0019_v04_recipes.py` | **2** | asset_recipes (B-11) |
| **0020** | `0020_v04_pgvector.py` | **3** | pgvector 확장 활성화 + blog_posts.embedding/guides.embedding (T-14) — assets.embedding은 0014에서 미리 컬럼만 추가, 인덱스는 여기서 |

---

## 2. 공통 컬럼·인덱스 패턴

### 2.1 모든 엔티티 공통

```sql
id            BIGSERIAL PRIMARY KEY,
created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

`updated_at` 자동 갱신 트리거:

```sql
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 각 테이블에 적용
CREATE TRIGGER trg_<table>_updated_at BEFORE UPDATE ON <table>
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

### 2.2 enum 표현 방식

PostgreSQL `ENUM` 타입 대신 **`VARCHAR + CHECK 제약`**을 사용한다. 이유: enum 변경(값 추가/삭제) 시 마이그레이션 부담이 큼.

```sql
status VARCHAR(32) NOT NULL CHECK (status IN ('pending','approved','rejected','published'))
```

---

## 3. users / 인증

### 3.1 `users`

```sql
CREATE TABLE users (
  id             BIGSERIAL PRIMARY KEY,
  email          VARCHAR(255) NOT NULL,
  email_lower    VARCHAR(255) GENERATED ALWAYS AS (LOWER(email)) STORED,
  password_hash  VARCHAR(255),                               -- OAuth 전용 사용자는 NULL 가능
  display_name   VARCHAR(60),
  locale         VARCHAR(10) NOT NULL DEFAULT 'ko',
  status         VARCHAR(32) NOT NULL DEFAULT 'active'
                 CHECK (status IN ('active','suspended','deleted')),
  email_verified_at  TIMESTAMPTZ,
  last_login_at      TIMESTAMPTZ,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_users_email_lower ON users (email_lower) WHERE status <> 'deleted';
CREATE INDEX idx_users_created_at ON users (created_at DESC);
CREATE INDEX idx_users_status ON users (status) WHERE status <> 'deleted';
```

> **소프트 삭제**: `status='deleted'`로 표시. unique 인덱스에 `WHERE status <> 'deleted'` 부분 인덱스로 복원 가능 동시에 새 가입 허용.

### 3.2 `email_verifications`

```sql
CREATE TABLE email_verifications (
  id           BIGSERIAL PRIMARY KEY,
  user_id      BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token        VARCHAR(64) NOT NULL,                         -- secrets.token_urlsafe(48)
  expires_at   TIMESTAMPTZ NOT NULL,                         -- 발급 + 24h
  used_at      TIMESTAMPTZ,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_email_verifications_token ON email_verifications (token);
CREATE INDEX idx_email_verifications_user ON email_verifications (user_id, used_at);
```

### 3.3 `password_resets`

```sql
CREATE TABLE password_resets (
  id           BIGSERIAL PRIMARY KEY,
  user_id      BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash   VARCHAR(255) NOT NULL,                        -- 토큰 자체는 저장 X, hash만
  expires_at   TIMESTAMPTZ NOT NULL,                         -- 발급 + 1h
  used_at      TIMESTAMPTZ,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_password_resets_user ON password_resets (user_id, used_at);
```

### 3.4 `sessions` — 서버 세션 (Auth.js v5)

> Auth.js v5(NextAuth)의 Database session을 사용. JWT 옵션도 가능하지만, 강제 로그아웃·세션 만료를 서버에서 통제하기 위해 DB 세션 채택.

```sql
CREATE TABLE sessions (
  id              BIGSERIAL PRIMARY KEY,
  session_token   VARCHAR(255) NOT NULL,
  user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires         TIMESTAMPTZ NOT NULL,
  user_agent      VARCHAR(500),
  ip              INET,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_sessions_token ON sessions (session_token);
CREATE INDEX idx_sessions_user ON sessions (user_id);
CREATE INDEX idx_sessions_expires ON sessions (expires);
```

### 3.5 `oauth_accounts` (Phase 2)

```sql
CREATE TABLE oauth_accounts (
  id                  BIGSERIAL PRIMARY KEY,
  user_id             BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  provider            VARCHAR(32) NOT NULL CHECK (provider IN ('google','kakao','github')),
  provider_account_id VARCHAR(255) NOT NULL,
  access_token        TEXT,
  refresh_token       TEXT,
  expires_at          TIMESTAMPTZ,
  scope               VARCHAR(500),
  token_type          VARCHAR(32),
  id_token            TEXT,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_oauth_provider_account ON oauth_accounts (provider, provider_account_id);
CREATE INDEX idx_oauth_user ON oauth_accounts (user_id);
```

---

## 4. 분류 (Categories / Tags)

### 4.1 `categories`

```sql
CREATE TABLE categories (
  id           BIGSERIAL PRIMARY KEY,
  parent_id    BIGINT REFERENCES categories(id) ON DELETE SET NULL,
  slug         VARCHAR(80) NOT NULL,
  name_ko      VARCHAR(80) NOT NULL,
  name_en      VARCHAR(80),
  name_ja      VARCHAR(80),
  description_ko TEXT,
  description_en TEXT,
  description_ja TEXT,
  sort_order   INT NOT NULL DEFAULT 0,
  is_active    BOOLEAN NOT NULL DEFAULT TRUE,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_categories_slug ON categories (slug);
CREATE INDEX idx_categories_parent ON categories (parent_id, sort_order);
CREATE INDEX idx_categories_active ON categories (is_active);
```

> 다국어 컬럼을 직접 두는 패턴(작은 도메인용). 큰 다국어 시스템은 `category_translations` 별도 테이블이 정석이지만, 카테고리는 100개 미만이라 인라인.

### 4.2 `tags`

```sql
CREATE TABLE tags (
  id           BIGSERIAL PRIMARY KEY,
  slug         VARCHAR(80) NOT NULL,
  name_ko      VARCHAR(80) NOT NULL,
  name_en      VARCHAR(80),
  name_ja      VARCHAR(80),
  use_count    INT NOT NULL DEFAULT 0,                       -- denormalized counter
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_tags_slug ON tags (slug);
CREATE INDEX idx_tags_use_count ON tags (use_count DESC);
```

### 4.3 `asset_tags` (다대다)

```sql
CREATE TABLE asset_tags (
  asset_id   BIGINT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
  tag_id     BIGINT NOT NULL REFERENCES tags(id)   ON DELETE CASCADE,
  PRIMARY KEY (asset_id, tag_id)
);

CREATE INDEX idx_asset_tags_tag ON asset_tags (tag_id);
```

---

## 5. assets (통합 자산)

### 5.1 `assets` (Phase 1: 이미지만 / Phase 2: 모든 타입)

```sql
CREATE TABLE assets (
  id                BIGSERIAL PRIMARY KEY,
  slug              VARCHAR(120) NOT NULL,                   -- URL용 고유 슬러그
  asset_type        VARCHAR(32) NOT NULL                     -- Phase 1: 'image'만
                    CHECK (asset_type IN (
                      'image','pptx','svg','docx','xlsx','html','lottie','colorbook','icon_set'
                    )),
  category_id       BIGINT REFERENCES categories(id) ON DELETE SET NULL,
  status            VARCHAR(32) NOT NULL DEFAULT 'inbox'
                    CHECK (status IN ('inbox','approved','published','rejected','archived')),

  -- 메타 (다국어는 asset_translations 사용. 단 핵심 검색 색인용 ko 필드는 여기 둠)
  title_ko          VARCHAR(200) NOT NULL,
  description_ko    TEXT,
  alt_text_ko       VARCHAR(500),

  -- 파일 정보 (대표 1개 — 같은 자산의 여러 변형은 asset_files에)
  file_path         VARCHAR(500),                            -- /var/lib/vaultix/assets/...
  thumbnail_path    VARCHAR(500),                            -- 썸네일 (320px 폭)
  preview_path      VARCHAR(500),                            -- 큰 미리보기 (1024px)
  file_size_bytes   BIGINT,
  mime_type         VARCHAR(80),
  width             INT,
  height            INT,
  aspect_ratio      VARCHAR(8),                              -- '1:1','3:2','2:3' 등
  duration_ms       INT,                                     -- 영상/Lottie 용 (Phase 5)

  -- 생성 정보
  ai_model          VARCHAR(80),                             -- 'nanobanana-vX','gpt-image-2','flux-dev' 등
  ai_generator      VARCHAR(40),                             -- 'nanobanana','gpt_image_2','comfy'
  generation_job_id BIGINT REFERENCES generation_jobs(id) ON DELETE SET NULL,
  generation_params JSONB NOT NULL DEFAULT '{}'::jsonb,      -- prompt/seed/cfg 등

  -- 점수·통계
  quality_score     NUMERIC(3,2),                            -- 0.00 ~ 1.00
  download_count    INT NOT NULL DEFAULT 0,
  view_count        INT NOT NULL DEFAULT 0,
  favorite_count    INT NOT NULL DEFAULT 0,

  -- 시간
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  approved_at       TIMESTAMPTZ,
  published_at      TIMESTAMPTZ,
  rejected_at       TIMESTAMPTZ,

  CONSTRAINT chk_quality_score CHECK (quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1))
);

CREATE UNIQUE INDEX uq_assets_slug ON assets (slug);
CREATE INDEX idx_assets_status_published ON assets (status, published_at DESC) WHERE status = 'published';
CREATE INDEX idx_assets_category ON assets (category_id, status);
CREATE INDEX idx_assets_type_status ON assets (asset_type, status);
CREATE INDEX idx_assets_published_at ON assets (published_at DESC) WHERE status = 'published';
CREATE INDEX idx_assets_download_count ON assets (download_count DESC) WHERE status = 'published';
CREATE INDEX idx_assets_inbox ON assets (created_at) WHERE status = 'inbox';

-- 한국어 전문 검색 (Phase 1 — title_ko + description_ko)
CREATE INDEX idx_assets_fts_ko ON assets
  USING GIN (to_tsvector('simple', COALESCE(title_ko,'') || ' ' || COALESCE(description_ko,'')))
  WHERE status = 'published';

-- generation_params JSONB 검색 (자주 사용 컬럼)
CREATE INDEX idx_assets_params_prompt ON assets USING GIN ((generation_params -> 'prompt'));
```

### 5.2 `asset_files` (Phase 1) — 같은 자산의 여러 파일 변형

PNG/WebP/PDF 등 같은 자산의 다중 포맷.

```sql
CREATE TABLE asset_files (
  id              BIGSERIAL PRIMARY KEY,
  asset_id        BIGINT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
  variant         VARCHAR(40) NOT NULL,                     -- 'original','webp','thumbnail','preview','pdf'
  file_path       VARCHAR(500) NOT NULL,
  file_size_bytes BIGINT NOT NULL,
  mime_type       VARCHAR(80) NOT NULL,
  width           INT,
  height          INT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_asset_files ON asset_files (asset_id, variant);
CREATE INDEX idx_asset_files_asset ON asset_files (asset_id);
```

### 5.3 `asset_translations` (Phase 2)

다국어 메타데이터.

```sql
CREATE TABLE asset_translations (
  asset_id    BIGINT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
  locale      VARCHAR(10) NOT NULL,                          -- 'ko','en','ja','zh-CN' 등
  title       VARCHAR(200) NOT NULL,
  description TEXT,
  alt_text    VARCHAR(500),
  source      VARCHAR(20) NOT NULL DEFAULT 'auto'            -- 'auto'|'manual'|'imported'
              CHECK (source IN ('auto','manual','imported')),
  translated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (asset_id, locale)
);

CREATE INDEX idx_asset_translations_locale ON asset_translations (locale);

-- 다국어 전문 검색 (locale별 인덱스)
-- Phase 2에서 next-intl 라우팅에 맞춰 추가
```

> Phase 1은 `assets.title_ko/description_ko/alt_text_ko`만 사용. Phase 2 마이그레이션 시 모든 row를 `asset_translations(locale='ko')`에 옮기고 assets의 _ko 컬럼은 유지(빠른 검색용 캐시).

---

## 6. downloads / favorites

### 6.1 `downloads`

```sql
CREATE TABLE downloads (
  id            BIGSERIAL PRIMARY KEY,
  user_id       BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  asset_id      BIGINT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
  asset_file_id BIGINT REFERENCES asset_files(id) ON DELETE SET NULL,
  bytes_sent    BIGINT NOT NULL,
  ip            INET NOT NULL,
  user_agent    VARCHAR(500),
  referer       VARCHAR(500),
  downloaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uq_downloads_user_asset UNIQUE (user_id, asset_id)
                                     -- 재다운로드는 새 row 생성 X. UPDATE bytes_sent + downloaded_at
);

CREATE INDEX idx_downloads_user_time ON downloads (user_id, downloaded_at DESC);
CREATE INDEX idx_downloads_asset_time ON downloads (asset_id, downloaded_at DESC);
CREATE INDEX idx_downloads_time ON downloads (downloaded_at DESC);
```

> **B-04 정책 구현**: 동일 (user_id, asset_id) 조합은 UPSERT. 새 다운로드는 카운트 X. 단 `bytes_sent`와 `downloaded_at`은 갱신.

```sql
-- 재다운로드 UPSERT
INSERT INTO downloads (user_id, asset_id, asset_file_id, bytes_sent, ip, user_agent)
VALUES (:user_id, :asset_id, :asset_file_id, :bytes, :ip, :ua)
ON CONFLICT (user_id, asset_id) DO UPDATE
SET bytes_sent = EXCLUDED.bytes_sent,
    downloaded_at = NOW();
```

> 시간당 30회 한도는 Redis(`dl:{user_id}:{YYYYMMDDHH}` INCR with TTL 3600)로 관리. DB 부담 회피.

### 6.2 `favorites` (Phase 2)

```sql
CREATE TABLE favorites (
  user_id    BIGINT NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
  asset_id   BIGINT NOT NULL REFERENCES assets(id)  ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, asset_id)
);

CREATE INDEX idx_favorites_user_time ON favorites (user_id, created_at DESC);
CREATE INDEX idx_favorites_asset ON favorites (asset_id);

-- assets.favorite_count 업데이트 트리거
CREATE OR REPLACE FUNCTION update_favorite_count()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE assets SET favorite_count = favorite_count + 1 WHERE id = NEW.asset_id;
  ELSIF TG_OP = 'DELETE' THEN
    UPDATE assets SET favorite_count = favorite_count - 1 WHERE id = OLD.asset_id;
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_favorites_count
AFTER INSERT OR DELETE ON favorites
FOR EACH ROW EXECUTE FUNCTION update_favorite_count();
```

---

## 7. 컬렉션 (Phase 2)

### 7.1 `collections` — 큐레이션 묶음 ("이번 주 트렌드", "비즈니스 베스트")

```sql
CREATE TABLE collections (
  id              BIGSERIAL PRIMARY KEY,
  slug            VARCHAR(120) NOT NULL,
  title_ko        VARCHAR(200) NOT NULL,
  title_en        VARCHAR(200),
  title_ja        VARCHAR(200),
  description_ko  TEXT,
  cover_asset_id  BIGINT REFERENCES assets(id) ON DELETE SET NULL,
  is_featured     BOOLEAN NOT NULL DEFAULT FALSE,
  sort_order      INT NOT NULL DEFAULT 0,
  status          VARCHAR(32) NOT NULL DEFAULT 'draft'
                  CHECK (status IN ('draft','published','archived')),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  published_at    TIMESTAMPTZ
);

CREATE UNIQUE INDEX uq_collections_slug ON collections (slug);
CREATE INDEX idx_collections_featured ON collections (is_featured, sort_order) WHERE status = 'published';
```

### 7.2 `collection_items`

```sql
CREATE TABLE collection_items (
  collection_id BIGINT NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
  asset_id      BIGINT NOT NULL REFERENCES assets(id)      ON DELETE CASCADE,
  sort_order    INT NOT NULL DEFAULT 0,
  added_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (collection_id, asset_id)
);

CREATE INDEX idx_collection_items_order ON collection_items (collection_id, sort_order);
```

---

## 8. 프롬프트 풀 (생성 자동화 핵심)

### 8.1 `prompt_templates`

```sql
CREATE TABLE prompt_templates (
  id                 BIGSERIAL PRIMARY KEY,
  name               VARCHAR(120) NOT NULL,                  -- 사람이 알아볼 식별자
  asset_type         VARCHAR(32) NOT NULL                    -- v0.3 §3 의 종류와 같음
                     CHECK (asset_type IN (
                       'image','pptx','svg','docx','xlsx','html','lottie','colorbook','icon_set'
                     )),
  category_id        BIGINT REFERENCES categories(id) ON DELETE SET NULL,

  -- 프롬프트 템플릿
  base_prompt        TEXT NOT NULL,                          -- "{subject}, {style}, {mood}, professional"
  negative_prompt    TEXT,
  variables_json     JSONB NOT NULL DEFAULT '{}'::jsonb,     -- {"subject":[...], "style":[...]}

  -- 생성 파라미터
  aspect_ratio       VARCHAR(8) NOT NULL DEFAULT '1:1',
  preferred_model    VARCHAR(80),                            -- 'flux-dev','sdxl-base' 등
  workflow_template  VARCHAR(120),                           -- 'flux_dev_basic_1024.json'

  -- 가중치 / 활성화
  weight             INT NOT NULL DEFAULT 100,                -- 1~100, 비활성=0
  performance_score  NUMERIC(5,2) NOT NULL DEFAULT 0,         -- 발행 후 다운로드 수 기반 자동 갱신
  is_active          BOOLEAN NOT NULL DEFAULT TRUE,

  -- 메타
  notes              TEXT,
  tags               VARCHAR(255)[],                          -- 운영 태그 (검색용)
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_prompt_templates_active ON prompt_templates (asset_type, is_active, weight);
CREATE INDEX idx_prompt_templates_category ON prompt_templates (category_id);
CREATE INDEX idx_prompt_templates_perf ON prompt_templates (performance_score DESC);
```

### 8.2 `generation_jobs`

```sql
CREATE TABLE generation_jobs (
  id                   BIGSERIAL PRIMARY KEY,
  prompt_template_id   BIGINT REFERENCES prompt_templates(id) ON DELETE SET NULL,

  -- 작업 입력
  asset_type           VARCHAR(32) NOT NULL,
  prompt_text          TEXT NOT NULL,
  negative_prompt      TEXT,
  aspect_ratio         VARCHAR(8) NOT NULL,
  seed                 BIGINT,
  generation_params    JSONB NOT NULL DEFAULT '{}'::jsonb,

  -- 상태 추적
  status               VARCHAR(32) NOT NULL DEFAULT 'queued'
                       CHECK (status IN (
                         'queued','generating_primary','generating_fallback',
                         'generated','validated','scored','metadata_done','published',
                         'failed','rejected_low_score'
                       )),
  generator            VARCHAR(40),                          -- 'nanobanana','gpt_image_2','comfy'
  attempts             INT NOT NULL DEFAULT 0,
  raw_path             VARCHAR(500),                         -- 생성 직후 PNG 경로
  error                VARCHAR(500),

  -- 결과 자산 연결 (성공 시)
  asset_id             BIGINT REFERENCES assets(id) ON DELETE SET NULL,

  -- 시간
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  started_at           TIMESTAMPTZ,
  completed_at         TIMESTAMPTZ,
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_generation_jobs_status_time ON generation_jobs (status, created_at);
CREATE INDEX idx_generation_jobs_template ON generation_jobs (prompt_template_id, created_at DESC);
CREATE INDEX idx_generation_jobs_generator_month
  ON generation_jobs (generator, created_at)
  WHERE generator IN ('nanobanana','gpt_image_2','comfy');   -- 호출량·장애 추적용
```

> **성능 점수 갱신**: cron으로 매일 새벽, 최근 30일 발행된 자산의 다운로드 수를 집계해 `prompt_templates.performance_score` 갱신.

```sql
-- 매일 04:00 cron
UPDATE prompt_templates pt
SET performance_score = COALESCE(sub.score, 0)
FROM (
  SELECT
    pt2.id AS template_id,
    AVG(a.download_count)::NUMERIC(5,2) AS score
  FROM prompt_templates pt2
  JOIN generation_jobs gj ON gj.prompt_template_id = pt2.id
  JOIN assets a ON a.generation_job_id = gj.id
  WHERE a.published_at > NOW() - INTERVAL '30 days'
  GROUP BY pt2.id
) sub
WHERE pt.id = sub.template_id;
```

---

## 9. 어드민 감사 로그

### 9.1 `admin_audit_logs`

```sql
CREATE TABLE admin_audit_logs (
  id           BIGSERIAL PRIMARY KEY,
  user_id      BIGINT REFERENCES users(id) ON DELETE SET NULL,
  action       VARCHAR(80) NOT NULL,                         -- 'asset.approve','asset.reject','user.suspend' 등
  target_type  VARCHAR(40),                                  -- 'asset','user','prompt_template'
  target_id    BIGINT,
  before_json  JSONB,
  after_json   JSONB,
  ip           INET,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_user_time ON admin_audit_logs (user_id, created_at DESC);
CREATE INDEX idx_audit_target ON admin_audit_logs (target_type, target_id, created_at DESC);
CREATE INDEX idx_audit_action ON admin_audit_logs (action, created_at DESC);

-- 6개월 이상 자동 삭제 (선택)
-- pg_cron 또는 외부 cron으로
```

---

## 10. 메타 콘텐츠 (Phase 3)

### 10.1 `topics`

```sql
CREATE TABLE topics (
  id                BIGSERIAL PRIMARY KEY,
  source            VARCHAR(40) NOT NULL                     -- 'trends_kr','trends_global','competitor','internal_search','llm_suggest'
                    CHECK (source IN ('trends_kr','trends_global','competitor','internal_search','llm_suggest')),
  raw_topic         VARCHAR(500) NOT NULL,
  normalized_topic  VARCHAR(500) NOT NULL,                   -- 정규화 (소문자, 공백 정리)
  score             NUMERIC(5,2) NOT NULL DEFAULT 0,         -- LLM 점수
  status            VARCHAR(32) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','approved','rejected','published','expired')),
  meta              JSONB NOT NULL DEFAULT '{}'::jsonb,      -- 검색량/경쟁도/추가 메모
  discovered_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  curated_at        TIMESTAMPTZ,
  curated_by        BIGINT REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_topics_status_score ON topics (status, score DESC);
CREATE INDEX idx_topics_source_time ON topics (source, discovered_at DESC);
CREATE INDEX idx_topics_normalized ON topics (normalized_topic);
```

### 10.2 `blog_posts`

```sql
CREATE TABLE blog_posts (
  id              BIGSERIAL PRIMARY KEY,
  slug            VARCHAR(120) NOT NULL,
  topic_id        BIGINT REFERENCES topics(id) ON DELETE SET NULL,
  category        VARCHAR(40) NOT NULL                       -- 'tool_review','guide','workflow','case_study','news'
                  CHECK (category IN ('tool_review','guide','workflow','case_study','news')),
  status          VARCHAR(32) NOT NULL DEFAULT 'draft'
                  CHECK (status IN ('draft','review','published','archived')),

  -- 콘텐츠
  draft_content     TEXT,                                    -- LLM이 생성한 초안 (마크다운)
  insight_content   TEXT,                                    -- JH가 추가한 인사이트 (마크다운)
  final_content     TEXT,                                    -- 통합·검수 완료된 본문 (마크다운)
  excerpt           VARCHAR(300),
  hero_asset_id     BIGINT REFERENCES assets(id) ON DELETE SET NULL,

  -- 메타
  reading_minutes   INT,                                     -- 자동 계산
  word_count        INT,
  ai_generated      BOOLEAN NOT NULL DEFAULT TRUE,
  manual_edited     BOOLEAN NOT NULL DEFAULT FALSE,

  -- SEO
  seo_title         VARCHAR(200),
  seo_description   VARCHAR(300),

  -- 시간
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  published_at      TIMESTAMPTZ
);

CREATE UNIQUE INDEX uq_blog_posts_slug ON blog_posts (slug);
CREATE INDEX idx_blog_posts_status_pub ON blog_posts (status, published_at DESC) WHERE status = 'published';
CREATE INDEX idx_blog_posts_category ON blog_posts (category, published_at DESC) WHERE status = 'published';
CREATE INDEX idx_blog_posts_topic ON blog_posts (topic_id);
CREATE INDEX idx_blog_fts ON blog_posts USING GIN (to_tsvector('simple', COALESCE(seo_title,'') || ' ' || COALESCE(final_content,''))) WHERE status = 'published';
```

### 10.3 `blog_post_translations` (Phase 3 — 다국어 블로그)

```sql
CREATE TABLE blog_post_translations (
  blog_post_id BIGINT NOT NULL REFERENCES blog_posts(id) ON DELETE CASCADE,
  locale       VARCHAR(10) NOT NULL,
  title        VARCHAR(200) NOT NULL,
  excerpt      VARCHAR(300),
  content      TEXT NOT NULL,
  source       VARCHAR(20) NOT NULL DEFAULT 'auto'
               CHECK (source IN ('auto','manual','imported')),
  translated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (blog_post_id, locale)
);

CREATE INDEX idx_blog_translations_locale ON blog_post_translations (locale);
```

### 10.4 `prompt_library_items` — 사용자 노출용 프롬프트 라이브러리

> 백엔드 자동 생성용 `prompt_templates`와 별개. 사용자가 복사해서 자기 도구에 쓰는 큐레이션 프롬프트.

```sql
CREATE TABLE prompt_library_items (
  id            BIGSERIAL PRIMARY KEY,
  slug          VARCHAR(120) NOT NULL,
  title_ko      VARCHAR(200) NOT NULL,
  description_ko TEXT,
  prompt_text   TEXT NOT NULL,                               -- 영어/한국어 둘 다 가능
  prompt_lang   VARCHAR(10) NOT NULL DEFAULT 'en',
  use_case      VARCHAR(40),                                 -- 'logo','illustration','poster','realistic_photo' 등
  recommended_models  VARCHAR(80)[],                         -- ['Flux','SDXL']
  example_asset_ids   BIGINT[],                              -- 결과 예시 자산 ids
  copy_count    INT NOT NULL DEFAULT 0,
  status        VARCHAR(32) NOT NULL DEFAULT 'published',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_prompt_library_slug ON prompt_library_items (slug);
CREATE INDEX idx_prompt_library_use_case ON prompt_library_items (use_case);
CREATE INDEX idx_prompt_library_copy ON prompt_library_items (copy_count DESC);
```

### 10.5 `tools` — AI 도구 디렉토리 (제휴/리뷰)

```sql
CREATE TABLE tools (
  id                BIGSERIAL PRIMARY KEY,
  slug              VARCHAR(120) NOT NULL,
  name              VARCHAR(120) NOT NULL,
  category          VARCHAR(40) NOT NULL,                    -- 'image_generator','llm','video','audio','design'
  description_ko    TEXT,
  url               VARCHAR(500) NOT NULL,
  affiliate_url     VARCHAR(500),                            -- 제휴 링크 (있으면)
  pricing_summary   VARCHAR(200),                            -- 'Free / $20 Pro' 등
  pros_ko           TEXT[],
  cons_ko           TEXT[],
  jh_rating         NUMERIC(2,1),                            -- 0.0 ~ 5.0
  jh_review_post_id BIGINT REFERENCES blog_posts(id) ON DELETE SET NULL,
  is_featured       BOOLEAN NOT NULL DEFAULT FALSE,
  status            VARCHAR(32) NOT NULL DEFAULT 'published',
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_tools_slug ON tools (slug);
CREATE INDEX idx_tools_category ON tools (category, is_featured DESC);
```

---

## 11. 뉴스레터 (Phase 3)

### 11.1 `newsletter_subscribers`

> Listmonk가 메인 저장소. vaultix DB에는 본인 사용자와 매핑·동기화 상태만 미러.

```sql
CREATE TABLE newsletter_subscribers (
  id              BIGSERIAL PRIMARY KEY,
  user_id         BIGINT REFERENCES users(id) ON DELETE SET NULL,
  email           VARCHAR(255) NOT NULL,
  email_lower     VARCHAR(255) GENERATED ALWAYS AS (LOWER(email)) STORED,
  status          VARCHAR(32) NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending','confirmed','unsubscribed','bounced')),
  source          VARCHAR(40),                               -- 'footer','blog_modal','signup_optin'
  listmonk_subscriber_id BIGINT,                             -- Listmonk 측 ID (sync)
  confirmed_at    TIMESTAMPTZ,
  unsubscribed_at TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_newsletter_email ON newsletter_subscribers (email_lower)
  WHERE status <> 'unsubscribed';
CREATE INDEX idx_newsletter_status ON newsletter_subscribers (status);
```

---

## 12. A/B 테스트 (Phase 4)

### 12.1 `ab_experiments`

```sql
CREATE TABLE ab_experiments (
  id           BIGSERIAL PRIMARY KEY,
  key          VARCHAR(80) NOT NULL,                         -- 'asset_card_v2','home_hero_b' 등
  description  TEXT,
  variants     JSONB NOT NULL DEFAULT '["control","treatment"]'::jsonb,
  status       VARCHAR(32) NOT NULL DEFAULT 'draft'
               CHECK (status IN ('draft','running','paused','completed','archived')),
  started_at   TIMESTAMPTZ,
  ended_at     TIMESTAMPTZ,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_ab_experiments_key ON ab_experiments (key);
```

### 12.2 `ab_assignments`

```sql
CREATE TABLE ab_assignments (
  experiment_id BIGINT NOT NULL REFERENCES ab_experiments(id) ON DELETE CASCADE,
  user_id       BIGINT REFERENCES users(id) ON DELETE CASCADE,
  anon_id       VARCHAR(64),                                  -- 비로그인 사용자의 쿠키 ID
  variant       VARCHAR(40) NOT NULL,
  assigned_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT chk_user_or_anon CHECK ((user_id IS NOT NULL) OR (anon_id IS NOT NULL)),
  CONSTRAINT uq_ab_user UNIQUE NULLS NOT DISTINCT (experiment_id, user_id),
  CONSTRAINT uq_ab_anon UNIQUE NULLS NOT DISTINCT (experiment_id, anon_id)
);

CREATE INDEX idx_ab_assignments_exp ON ab_assignments (experiment_id, variant);
```

---

## 13. 인덱스 점검 체크리스트 (Phase 1 W2 마지막 점검)

| 쿼리 패턴 | 인덱스 | 비고 |
|----------|--------|------|
| 홈 — 최신 published 자산 12개 | `idx_assets_published_at` | partial WHERE published |
| 카테고리 — 자산 페이지네이션 | `idx_assets_category` | (category_id, status) |
| 검색 (한국어) | `idx_assets_fts_ko` GIN | tsvector |
| 자산 상세 — slug 조회 | `uq_assets_slug` | unique |
| 큐레이션 인박스 — inbox 정렬 | `idx_assets_inbox` | partial WHERE inbox |
| 사용자 다운로드 내역 | `idx_downloads_user_time` | desc |
| 시간당 다운로드 한도 | (Redis, DB 인덱스 불필요) | - |
| 비용 캡 (월 외부 API 호출 수) | `idx_generation_jobs_generator_month` | partial |

---

## 14. 백업·복원 (참고)

- `pg_dump` 일 1회 cron → `/var/lib/vaultix/backup/pg-YYYYMMDD-HHMM.dump.gz`
- restic으로 gdrive에 증분 백업 (Phase 0의 backup.sh 참조)
- 복원 절차는 A6 운영 런북에 상세 기재

---

## 15. ER 다이어그램 (텍스트)

```
users ─┬─< sessions
       ├─< oauth_accounts (Phase 2)
       ├─< email_verifications
       ├─< password_resets
       ├─< downloads >─ assets >─ asset_files
       ├─< favorites (Phase 2) >─ assets
       └─< admin_audit_logs (admin)

assets >─ categories
       >─ generation_jobs >─ prompt_templates
       <─ asset_tags >─ tags
       <─ asset_translations (Phase 2)
       <─ collection_items >─ collections (Phase 2)

topics >─ blog_posts (Phase 3)
                >─ blog_post_translations
                >─ assets (hero_asset)

prompt_library_items (사용자 노출용, Phase 3)
tools (Phase 3)
newsletter_subscribers (Phase 3)
ab_experiments >─< ab_assignments (Phase 4)
```

---

## 16. SQLAlchemy 모델 매핑 (예시 — Phase 1 핵심만)

```python
# apps/api/src/vaultix_api/models/asset.py
from datetime import datetime
from sqlalchemy import (
    BigInteger, String, Text, Integer, ForeignKey, DateTime, Numeric, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from vaultix_api.db.base import Base


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False)
    category_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("categories.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="inbox")

    title_ko: Mapped[str] = mapped_column(String(200), nullable=False)
    description_ko: Mapped[str | None] = mapped_column(Text)
    alt_text_ko: Mapped[str | None] = mapped_column(String(500))

    file_path: Mapped[str | None] = mapped_column(String(500))
    thumbnail_path: Mapped[str | None] = mapped_column(String(500))
    preview_path: Mapped[str | None] = mapped_column(String(500))
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    mime_type: Mapped[str | None] = mapped_column(String(80))
    width: Mapped[int | None]
    height: Mapped[int | None]
    aspect_ratio: Mapped[str | None] = mapped_column(String(8))

    ai_model: Mapped[str | None] = mapped_column(String(80))
    ai_generator: Mapped[str | None] = mapped_column(String(40))
    generation_job_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("generation_jobs.id", ondelete="SET NULL"))
    generation_params: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    quality_score: Mapped[float | None] = mapped_column(Numeric(3, 2))
    download_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    favorite_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("status IN ('inbox','approved','published','rejected','archived')"),
        CheckConstraint("quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)"),
    )
```

(다른 모델은 같은 패턴 — Phase 1 W1~W2에서 일괄 작성)

---

## 17. v0.4 보강 — 신규 테이블·컬럼 (99B + A7 반영)

> **목적**: D-13(LLM 정책 변경), D-14(이미지 라우팅 변경), 99B 보강 결정(T-10·T-11·T-12·T-14·B-09·B-11·B-13)에서 추가된 데이터 모델을 한 곳에 정리.
> **마이그레이션**: §1의 0013~0020 리비전.

### 17.1 `cost_meter` — LLM/이미지/외부 API 호출량 추적 (T-10)

```sql
CREATE TABLE cost_meter (
  id              BIGSERIAL PRIMARY KEY,
  service         VARCHAR(40) NOT NULL,       -- 'nanobanana','gpt_image_2','comfyui',
                                              -- 'anthropic','openai','google_ai','zai','deepl' 등
  period          VARCHAR(10) NOT NULL,        -- 'YYYY-MM-DD' 일별 또는 'YYYY-MM' 월별
  call_count      INT NOT NULL DEFAULT 0,
  input_tokens    BIGINT NOT NULL DEFAULT 0,
  output_tokens   BIGINT NOT NULL DEFAULT 0,
  estimated_usd   NUMERIC(10,4) NOT NULL DEFAULT 0,   -- 참고용 (무제한 키이므로 강제력 없음)
  soft_limit      INT,                                -- 비정상 폭증 감지 임계 (선택)
  alert_at_50     BOOLEAN NOT NULL DEFAULT FALSE,
  alert_at_80     BOOLEAN NOT NULL DEFAULT FALSE,
  alert_at_100    BOOLEAN NOT NULL DEFAULT FALSE,
  last_alert_at   TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_cost_meter_service_period ON cost_meter (service, period);
CREATE INDEX idx_cost_meter_period ON cost_meter (period DESC);
```

> **운영**: 호출 1건당 UPSERT (service+period 키). 어드민 대시보드 위젯에서 `period = TO_CHAR(NOW(), 'YYYY-MM-DD')` 행 조회.

### 17.2 `llm_call_log` — 모든 LLM 호출 기록 (A7 §3.2)

```sql
CREATE TABLE llm_call_log (
  id              BIGSERIAL PRIMARY KEY,
  task_type       VARCHAR(50) NOT NULL,        -- 'metadata_gen','categorize','translate_nuance',
                                               -- 'blog_draft','insight_merge','topic_score','report_classify'
  provider        VARCHAR(20) NOT NULL,         -- 'anthropic','openai','google_ai','zai','local'
  model           VARCHAR(80) NOT NULL,
  input_tokens    INTEGER,
  output_tokens   INTEGER,
  latency_ms      INTEGER,
  cost_estimate_usd NUMERIC(10,6),
  success         BOOLEAN NOT NULL,
  error_kind      VARCHAR(50),                  -- 'rate_limit','timeout','5xx','auth_error','other'
  failover_from   VARCHAR(80),                  -- 폴백된 경우 원래 시도한 모델
  request_id      VARCHAR(64),                  -- 추적용 UUID
  related_asset_id BIGINT REFERENCES assets(id) ON DELETE SET NULL,
  related_blog_id  BIGINT REFERENCES blog_posts(id) ON DELETE SET NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_llm_log_task_time ON llm_call_log (task_type, created_at DESC);
CREATE INDEX idx_llm_log_model_time ON llm_call_log (model, created_at DESC) WHERE success = false;
CREATE INDEX idx_llm_log_failover ON llm_call_log (failover_from, created_at DESC) WHERE failover_from IS NOT NULL;
CREATE INDEX idx_llm_log_request ON llm_call_log (request_id) WHERE request_id IS NOT NULL;

-- 90일 이상 자동 삭제 (선택, pg_cron)
```

### 17.3 `asset_metrics_daily` — 자산 일별 메트릭 (T-12)

```sql
CREATE TABLE asset_metrics_daily (
  asset_id            BIGINT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
  metric_date         DATE NOT NULL,
  views               INT NOT NULL DEFAULT 0,
  download_starts     INT NOT NULL DEFAULT 0,
  downloads_completed INT NOT NULL DEFAULT 0,
  shares              INT NOT NULL DEFAULT 0,
  reports             INT NOT NULL DEFAULT 0,
  ctr                 NUMERIC(5,4) GENERATED ALWAYS AS (
                        CASE WHEN views > 0 THEN downloads_completed::NUMERIC / views ELSE 0 END
                      ) STORED,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (asset_id, metric_date)
);

CREATE INDEX idx_asset_metrics_date ON asset_metrics_daily (metric_date DESC);
CREATE INDEX idx_asset_metrics_ctr ON asset_metrics_daily (metric_date, ctr DESC);
```

> **집계**: API 핸들러에서 INCR 카운터(Redis) → 일 1회 cron이 `asset_metrics_daily`에 flush. `assets.download_count`/`view_count`는 동기 갱신(고비용 X — 롤백 가능).

### 17.4 `takedown_requests` — 신고 요청 (B-09)

```sql
CREATE TABLE takedown_requests (
  id                BIGSERIAL PRIMARY KEY,
  ticket_number     VARCHAR(20) NOT NULL,             -- 'TD-2026-000001'
  reporter_name     VARCHAR(120) NOT NULL,
  reporter_email    VARCHAR(255) NOT NULL,
  reporter_phone    VARCHAR(40),
  asset_id          BIGINT REFERENCES assets(id) ON DELETE SET NULL,
  asset_url         VARCHAR(500) NOT NULL,            -- 자산 삭제돼도 보존
  report_type       VARCHAR(40) NOT NULL              -- 'copyright','portrait_right','trademark','defamation','other'
                    CHECK (report_type IN ('copyright','portrait_right','trademark','defamation','other')),
  evidence_path     VARCHAR(500),                     -- 증빙 파일 경로 (5MB까지)
  statement         TEXT NOT NULL,                    -- 신고자 진술
  honest_filing     BOOLEAN NOT NULL DEFAULT FALSE,   -- "선의의 신고" 동의 체크
  status            VARCHAR(32) NOT NULL DEFAULT 'received'
                    CHECK (status IN ('received','reviewing','additional_info_requested','accepted','rejected','withdrawn')),
  resolution        TEXT,                             -- JH의 처리 결과 메모
  reviewed_by       BIGINT REFERENCES users(id) ON DELETE SET NULL,
  received_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  resolved_at       TIMESTAMPTZ,
  ip                INET,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_takedown_ticket ON takedown_requests (ticket_number);
CREATE INDEX idx_takedown_status_time ON takedown_requests (status, received_at DESC);
CREATE INDEX idx_takedown_asset ON takedown_requests (asset_id);
CREATE INDEX idx_takedown_reporter ON takedown_requests (reporter_email, received_at DESC);
```

### 17.5 `blocked_recipes` — 차단된 프롬프트/시드 조합 (B-09)

```sql
CREATE TABLE blocked_recipes (
  id              BIGSERIAL PRIMARY KEY,
  prompt_pattern  TEXT NOT NULL,                       -- 정확 매칭 또는 정규식
  pattern_type    VARCHAR(20) NOT NULL DEFAULT 'exact'
                  CHECK (pattern_type IN ('exact','contains','regex','seed')),
  model_name      VARCHAR(100),                        -- NULL이면 모든 모델
  seed            BIGINT,                              -- pattern_type='seed'일 때만
  reason          VARCHAR(40) NOT NULL                 -- 'takedown','manual_block','automated_filter','copyright_concern'
                  CHECK (reason IN ('takedown','manual_block','automated_filter','copyright_concern')),
  takedown_id     BIGINT REFERENCES takedown_requests(id) ON DELETE SET NULL,
  blocked_by      BIGINT REFERENCES users(id) ON DELETE SET NULL,
  notes           TEXT,
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at      TIMESTAMPTZ                          -- 영구 차단은 NULL
);

CREATE INDEX idx_blocked_recipes_active ON blocked_recipes (is_active, pattern_type);
CREATE INDEX idx_blocked_recipes_seed ON blocked_recipes (seed) WHERE seed IS NOT NULL;
CREATE INDEX idx_blocked_recipes_pattern ON blocked_recipes USING GIN (to_tsvector('simple', prompt_pattern));
```

> **운영**: 자산 발행 파이프라인이 매번 active blocked_recipes와 대조. 일치하면 자동 폐기 + admin_audit_logs 기록.

### 17.6 `daily_logs` — 운영 일지 + 오늘의 큐레이션 (B-13)

```sql
CREATE TABLE daily_logs (
  log_date          DATE PRIMARY KEY,
  -- 자동 채워지는 통계 (cron)
  assets_published  INT NOT NULL DEFAULT 0,
  downloads_total   INT NOT NULL DEFAULT 0,
  new_signups       INT NOT NULL DEFAULT 0,
  new_categories    INT NOT NULL DEFAULT 0,
  blog_posts_published INT NOT NULL DEFAULT 0,
  -- JH 수동 입력 (선택)
  jh_note           TEXT,                              -- "오늘은 미니멀 PPT 발행이 잘됨"
  experiments_tried JSONB NOT NULL DEFAULT '[]'::jsonb, -- 시도한 새 워크플로우 (실패 포함)
  -- 오늘의 큐레이션 (B-13 /today 페이지)
  curated_asset_ids BIGINT[] NOT NULL DEFAULT '{}',     -- JH가 오늘 ★ 표시한 자산 8~12개
  curated_comments  JSONB NOT NULL DEFAULT '{}'::jsonb, -- {"asset_id": "한 줄 코멘트"} 매핑
  is_published      BOOLEAN NOT NULL DEFAULT FALSE,    -- /today 페이지 노출 여부
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_daily_logs_published ON daily_logs (log_date DESC) WHERE is_published = true;
```

### 17.7 `asset_recipes` — 자산 레시피 공개 (B-11) ★★★

```sql
CREATE TABLE asset_recipes (
  asset_id         BIGINT PRIMARY KEY REFERENCES assets(id) ON DELETE CASCADE,
  model_name       VARCHAR(100) NOT NULL,              -- 'sdxl-base-1.0','flux.1-dev','nanobanana-v3','gpt-image-2'
  model_version    VARCHAR(50),
  generator        VARCHAR(40) NOT NULL,                -- 'comfyui','nanobanana','gpt_image_2'
  prompt_positive  TEXT NOT NULL,
  prompt_negative  TEXT,
  seed             BIGINT,
  cfg_scale        NUMERIC(4,2),
  steps            INTEGER,
  sampler          VARCHAR(50),
  workflow_json    JSONB,                              -- ComfyUI 워크플로우 전체 (특수 워크플로우만)
  workflow_template VARCHAR(120),                       -- 'consistent_character.json' 등
  license          VARCHAR(20) NOT NULL DEFAULT 'CC0',  -- 레시피 자체는 CC0
  view_count       INT NOT NULL DEFAULT 0,              -- 레시피 본 횟수
  copy_count       INT NOT NULL DEFAULT 0,              -- 프롬프트 복사 클릭
  workflow_download_count INT NOT NULL DEFAULT 0,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_asset_recipes_model ON asset_recipes (model_name);
CREATE INDEX idx_asset_recipes_copy ON asset_recipes (copy_count DESC);
CREATE INDEX idx_asset_recipes_workflow ON asset_recipes (workflow_template) WHERE workflow_template IS NOT NULL;
```

### 17.8 `assets` 테이블 v0.4 컬럼 추가

§5.1 assets 테이블에 다음 컬럼 추가 (마이그레이션 0014):

```sql
ALTER TABLE assets
  ADD COLUMN checksum             VARCHAR(64),         -- SHA-256 (T-11 자산 손상 감지)
  ADD COLUMN first_download_at    TIMESTAMPTZ,         -- T-12 Time-to-First-Download
  ADD COLUMN embedding            VECTOR(384),         -- T-14 자산↔가이드 매칭 (pgvector)
  ADD COLUMN taken_down_at        TIMESTAMPTZ,         -- B-09 비공개 처리 시점
  ADD COLUMN taken_down_reason    VARCHAR(255);

-- status enum에 'taken_down' 추가
ALTER TABLE assets DROP CONSTRAINT IF EXISTS assets_status_check;
ALTER TABLE assets ADD CONSTRAINT assets_status_check
  CHECK (status IN ('inbox','approved','published','rejected','archived','taken_down'));

CREATE INDEX idx_assets_checksum ON assets (checksum) WHERE checksum IS NOT NULL;
CREATE INDEX idx_assets_first_dl ON assets (first_download_at) WHERE first_download_at IS NOT NULL;
-- 임베딩 인덱스는 0020에서 (pgvector 활성화 후)
-- CREATE INDEX idx_assets_embedding ON assets USING hnsw (embedding vector_cosine_ops);
```

### 17.9 `generation_jobs` 테이블 v0.4 변경 (D-14 반영)

§8.2의 generation_jobs를 다음과 같이 수정 (마이그레이션 0015):

```sql
-- status enum 확장
ALTER TABLE generation_jobs DROP CONSTRAINT IF EXISTS generation_jobs_status_check;
ALTER TABLE generation_jobs ADD CONSTRAINT generation_jobs_status_check
  CHECK (status IN (
    'queued','queued_special',
    'generating_primary','generating_secondary','generating_special',
    'generated','validated','scored','metadata_done','published',
    'failed','rejected_low_score'
  ));

-- generator enum (CHECK는 없지만 코드에서 사용) — 값 변경 안내
-- 새 값: 'nanobanana','gpt_image_2','comfyui'
-- 폐기: 'replicate','fal'

-- 특수 워크플로우 컬럼
ALTER TABLE generation_jobs
  ADD COLUMN workflow_template VARCHAR(120),            -- 'consistent_character.json' 등
  ADD COLUMN workflow_params   JSONB,                   -- 특수 워크플로우 파라미터
  ADD COLUMN parent_asset_id   BIGINT REFERENCES assets(id) ON DELETE SET NULL,  -- 시리즈/변형 자산의 부모
  ADD COLUMN job_kind          VARCHAR(20) NOT NULL DEFAULT 'general'
    CHECK (job_kind IN ('general','special'));

-- 기존 인덱스 폐기 (Replicate/fal 비용 캡 계산용 — 무제한 키로 무의미)
DROP INDEX IF EXISTS idx_generation_jobs_generator_month;

-- 새 인덱스
CREATE INDEX idx_generation_jobs_kind_status ON generation_jobs (job_kind, status, created_at);
CREATE INDEX idx_generation_jobs_parent ON generation_jobs (parent_asset_id) WHERE parent_asset_id IS NOT NULL;
```

### 17.10 pgvector 확장 활성화 (마이그레이션 0020)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- assets.embedding은 0014에서 컬럼만 추가, 여기서 인덱스 생성
CREATE INDEX idx_assets_embedding ON assets
  USING hnsw (embedding vector_cosine_ops)
  WHERE status = 'published' AND embedding IS NOT NULL;

-- blog_posts에도 임베딩 추가 (T-14)
ALTER TABLE blog_posts ADD COLUMN embedding VECTOR(384);
CREATE INDEX idx_blog_posts_embedding ON blog_posts
  USING hnsw (embedding vector_cosine_ops)
  WHERE status = 'published' AND embedding IS NOT NULL;

-- 가이드 테이블 (Phase 3에 작성, 임시 placeholder)
-- prompt_library_items / tools에는 embedding 추가 안 함 (필요 시 별도 결정)
```

### 17.11 ER 다이어그램 보강

```
v0.4 신규/변경 관계:

assets ─< asset_metrics_daily   (T-12)
assets ─< asset_recipes (1:1)   (B-11)
assets ─< takedown_requests     (B-09)

takedown_requests >─ blocked_recipes  (B-09 자동 차단)
blog_posts ─< llm_call_log     (A7 D-13)
assets ─< llm_call_log         (A7 D-13)

cost_meter (단독, period 키)
daily_logs (단독, log_date 키)
```

---

## 18. 다음 문서로 이어지는 결정

- 위 모든 테이블의 CRUD 엔드포인트 → A2 API 스펙 §3~§9 + v0.4 §10
- `prompt_templates`, `generation_jobs` 워커 사용 → A3 §5~§6 / Phase 1 §W6
- `assets.title_ko/description_ko` → 자동 메타데이터 생성 (외부 LLM API 라우팅, A7 §2 #1) → Phase 1 §W7
- `downloads`의 시간당 한도 (Redis) → Phase 1 §W3 다운로드 핸들러
- **(v0.4)** `cost_meter`/`llm_call_log` → 어드민 대시보드 위젯 (T-12) + Telegram 알림
- **(v0.4)** `asset_metrics_daily` → /admin/dashboard 위젯
- **(v0.4)** `takedown_requests` → /report 페이지 + /admin/takedowns 처리 화면
- **(v0.4)** `asset_recipes` → 자산 상세 페이지 레시피 섹션 + 워크플로우 JSON 다운로드 엔드포인트
- **(v0.4)** `daily_logs` → /today, /log 공개 페이지 + 어드민 큐레이션 ★ 토글 인터랙션
- **(v0.4)** `assets.embedding`/`blog_posts.embedding` → 자산↔블로그 자동 추천 컴포넌트 (Phase 3)

