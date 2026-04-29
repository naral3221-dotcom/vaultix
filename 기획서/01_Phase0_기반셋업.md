# Phase 0 — 기반 셋업 상세 기획서

> **목적**: Phase 1~5 작업이 시작될 수 있는 인프라/저장소/CI/CD/모니터링/외부 모델 라우팅 기반을 확보한다.
> **작성일**: 2026-04-27
> **선행 조건**: 확정사항 레지스트리 D-1~D-21 확인, main-hub VPS 접속 가능, 외부 모델 API 키 확보
> **v0.4 기준**: Vaultix 저장소(`https://github.com/naral3221-dotcom/vaultix.git`)를 사용한다. Ollama 컨테이너/Replicate/fal.ai는 폐기된 결정이며, `C:\AI\llm`의 GGUF 모델은 MVP 기본 라우팅에 넣지 않는다. 충돌 시 `00_IMPLEMENTATION_SPEC_v0.4.md`와 A7을 우선한다.

---

## 1. 목표 & 완료 조건

### 1.1 목표

`git push`만으로 5분 이내에 main-hub VPS에 자동 배포되고, 모든 헬스체크가 통과하며, 어드민·DB GUI·Plausible·운영 대시보드가 Tailscale 대역에서 접근 가능한 상태를 만든다.

### 1.2 완료 조건 (체크리스트)

- [ ] 도커 네트워크 `vaultix_internal`(172.25.0.0/16) 생성 및 구동
- [ ] PostgreSQL 17 컨테이너 5440 포트로 구동 + cloudbeaver 등록 + 첫 마이그레이션 적용
- [ ] Redis 7 컨테이너 6380 포트로 구동
- [ ] FastAPI "hello world" 컨테이너가 127.0.0.1:8302에 헬스체크 응답
- [ ] Next.js "hello world" 컨테이너가 127.0.0.1:8301에 헬스체크 응답
- [ ] 시스템 nginx에 `vaultix.conf` 등록 + 임시 도메인(또는 Tailscale 호스트명)으로 https 접속 OK
- [ ] GitHub 저장소 `vaultix` 셋업 + Actions self-hosted runner가 main-hub에 등록
- [ ] `git push origin main` → CI 빌드 → main-hub에 docker compose pull/up → 5분 이내 반영
- [ ] Sentry 프로젝트 2개(api, web) 생성, DSN 환경변수 등록, 의도적 에러 발생 시 Sentry에 도착
- [ ] Plausible 셀프호스트 컨테이너 구동 + Tailscale 전용 노출
- [ ] Uptime Kuma 컨테이너 구동 + 모든 컨테이너 + 외부 통신(Resend/Nanobanana/OpenAI Image) 모니터 등록
- [ ] A7 기준 LLM 라우터 환경변수 등록(Anthropic/OpenAI/Google AI/Z.AI) + provider별 smoke test
- [ ] 이미지 라우팅 환경변수 등록(Nanobanana, OpenAI `gpt-image-2`) + 생성 API smoke test
- [ ] 데스크탑 ComfyUI ↔ VPS Tailscale 헬스체크 확인(특수 워크플로우용, Phase 1 일반 생성에는 사용하지 않음)
- [ ] `/admin/dashboard` v0(read-only 5개 위젯)와 `/admin/panic` 백엔드 플래그 골격 준비
- [ ] gdrive rclone 백업 스크립트 작동 + 첫 백업 파일 gdrive에 도착 확인
- [ ] pgBackRest 또는 wal-g WAL 아카이빙 PoC 완료 (RPO 1h 목표)
- [ ] sshd 설정 점검 완료 (PasswordAuthentication 명시 처리)
- [ ] 위 모든 항목이 1주일간 안정 가동 (Uptime Kuma 99% 이상)

---

## 2. 작업 분해 (WBS)

> 각 항목은 체크박스로 진행 추적. 의존성은 → 표기.
> 그룹(W0~W3)은 **묶음 단위**일 뿐 일정 약속이 아닙니다. (D-9)

### 2.1 사전 준비

- [ ] **A.1** GitHub Org/계정에서 `vaultix` 저장소 확인 및 clone URL 고정: `https://github.com/naral3221-dotcom/vaultix.git`
- [ ] **A.2** main-hub에서 `gh CLI` 설치 (`apt install gh`) — 토큰 로그인
- [ ] **A.3** main-hub에 `pnpm` 설치 (`npm i -g pnpm`)
- [ ] **A.4** main-hub에 `restic` 설치 (`apt install restic`) → A.10 에서 사용
- [ ] **A.5** sshd 설정 점검: `/etc/ssh/sshd_config`에 `PasswordAuthentication no` + `PermitRootLogin no` 명시 → 재시작
- [ ] **A.6** ufw 점검: 22/80/443 외 모든 인바운드 차단 확인 (이미 OK)
- [ ] **A.7** 데스크탑 Tailscale 설치 + 같은 tailnet 가입 확인 (`tailscale ping main-hub` 응답 확인)
- [ ] **A.8** 도메인 임시 결정: Phase 0~1 중에는 Tailscale 호스트명 또는 `vaultix.local` 같은 hosts 매핑, 또는 `vaultix.dev` 같은 임시 서브도메인 사용
- [ ] **A.9** 호스트 디렉토리 생성: `sudo mkdir -p /var/lib/vaultix/{postgres,redis,assets,plausible,listmonk,backup}` + `sudo chown -R 1001:1001 /var/lib/vaultix`
- [ ] **A.10** restic 백업 리포지토리 초기화: `/mnt/gdrive/vaultix-backup/`

### 2.2 저장소 구조 셋업

- [ ] **B.1** 로컬에서 `vaultix` clone → 모노레포 구조 생성 (§4.1 참조)
- [ ] **B.2** `.gitignore`, `.editorconfig`, `LICENSE`, `README.md` 작성
- [ ] **B.3** Renovate 설정 (`.github/renovate.json`)
- [ ] **B.4** pre-commit hook 설정 (ruff, eslint, prettier, secret scan)
- [ ] **B.5** `direnv` + `.envrc` (선택) — 로컬 dev에서 환경변수 자동 로드
- [ ] **B.6** `git push origin main` (빈 상태로 push 테스트)

### 2.3 도커 인프라

- [ ] **C.1** `docker network create --subnet=172.25.0.0/16 vaultix_internal`
- [ ] **C.2** `infra/docker-compose.yml` 작성 (§4.2 참조)
- [ ] **C.3** `.env.example` 작성 + `.env`는 main-hub에만 수동 배치 (gitignore)
- [ ] **C.4** PostgreSQL 17 컨테이너 구동 → `psql` 또는 cloudbeaver로 접속 확인
- [ ] **C.5** Redis 7 컨테이너 구동 → `redis-cli ping` 응답 확인
- [ ] **C.6** 외부 모델 라우터 smoke test → A7 provider별 API 키와 timeout/failover 설정 확인
- [ ] **C.6-1** 로컬 LLM 확인: `C:\AI\llm`은 GGUF/LM Studio 계열 저장소로 기록만 한다. Ollama service/env는 작성하지 않는다.
- [ ] **C.7** Plausible 컨테이너 구동 (DB는 별도 컨테이너 — Plausible은 ClickHouse 필요)
- [ ] **C.8** Uptime Kuma 컨테이너 구동
- [ ] **C.9** Listmonk 컨테이너 구동 (Phase 2에서 활용, Phase 0은 hello world만)

### 2.4 애플리케이션 골격

- [ ] **D.1** `apps/api/` FastAPI 프로젝트 초기화 (uv 사용, Python 3.12)
- [ ] **D.2** `/healthz` 엔드포인트 구현
- [ ] **D.3** Alembic 초기화 + `alembic upgrade head` 동작 확인
- [ ] **D.4** Sentry SDK 통합 + 의도적 에러 테스트
- [ ] **D.5** Dockerfile 작성 (multi-stage, distroless 또는 python:3.12-slim)
- [ ] **D.6** `apps/web/` Next.js 14+ 프로젝트 초기화 (pnpm)
- [ ] **D.7** App Router 기반 `/healthz` 페이지
- [ ] **D.8** Sentry SDK 통합 (next-sentry)
- [ ] **D.9** Dockerfile 작성 (next standalone output)

### 2.5 nginx + TLS + Tailscale 노출

- [ ] **E.1** `infra/nginx/vaultix.conf` 작성 (§4.3 참조)
- [ ] **E.2** main-hub: `sudo cp vaultix.conf /etc/nginx/sites-available/` + `sudo ln -s ... sites-enabled/`
- [ ] **E.3** `sudo nginx -t && sudo nginx -s reload`
- [ ] **E.4** certbot으로 임시 도메인 인증서 발급 (`certbot --nginx -d vaultix.example.com`)
- [ ] **E.5** Tailscale 전용 server block(`/etc/nginx/sites-available/vaultix-admin.conf`) 작성 — `allow 100.64.0.0/10; deny all;` 적용
- [ ] **E.6** 휴대폰/외부에서 `/admin/*` 접속 → 403 확인 / Tailscale 통해 접속 → 200 확인

### 2.6 CI/CD

- [ ] **F.1** GitHub Actions self-hosted runner를 main-hub에 설치 + systemd 서비스화
  - 사용자: `runner` (별도 계정), docker 그룹 가입
  - 작업 디렉토리: `/home/runner/_work`
- [ ] **F.2** `.github/workflows/ci.yml` 작성 — main 브랜치 push 시 빌드/테스트
  - api: `uv run pytest`
  - web: `pnpm test`, `pnpm build`
  - 이미지 빌드: `docker build -t ghcr.io/{org}/vaultix-api:${{ sha }} ...`
  - 푸시: GHCR
- [ ] **F.3** `.github/workflows/deploy.yml` 작성 — CI 통과 후 self-hosted runner가 deploy
  - `cd /home/openclaw/vaultix && git pull`
  - `docker compose pull && docker compose up -d`
  - 헬스체크 폴링 (30초 내 healthy 안 되면 롤백)
- [ ] **F.4** `git push` 테스트 → 5분 내 배포 확인
- [ ] **F.5** 의도적 빌드 실패 → 배포 미진행 + Slack/Telegram 알림 (선택)

### 2.7 백업/복원

- [ ] **G.1** `infra/scripts/backup.sh` 작성:
  - `pg_dump` → `/var/lib/vaultix/backup/pg-$(date).sql.gz`
  - assets 디렉토리 → restic 증분 백업 → `/mnt/gdrive/vaultix-backup/`
- [ ] **G.2** crontab: `0 4 * * * /opt/vaultix/scripts/backup.sh >> /var/log/vaultix/backup.log 2>&1`
- [ ] **G.3** 첫 백업 실행 후 gdrive에 파일 도착 확인
- [ ] **G.4** 복원 테스트 절차 문서화 (A6_운영_런북.md에 작성) + 실제 복원 1회 수행

### 2.8 이미지 라우팅 PoC

- [ ] **H.0** Nanobanana API 1장 생성 → 저장 → 썸네일 변환까지 확인
- [ ] **H.0-2** OpenAI `gpt-image-2` 1장 생성 → 저장 → 썸네일 변환까지 확인

- [ ] **H.1** 데스크탑 ComfyUI를 외부 인터페이스에 바인딩: `python main.py --listen 0.0.0.0 --port 8188`
- [ ] **H.2** 데스크탑 Windows 방화벽: Tailscale 인터페이스에서 8188 인바운드 허용
- [ ] **H.3** main-hub에서 `curl http://<desktop-tailscale-ip>:8188/system_stats` → 200 확인
- [ ] **H.4** main-hub에서 간단한 워크플로우 JSON POST → 이미지 생성 → `/view`로 다운로드 → 정상 PNG 확인 (특수 워크플로우 PoC)
- [ ] **H.5** 라운드트립 시간 측정 (장당 생성 + 전송 시간) → 특수 워크플로우 베이스라인 기록

### 2.9 모니터링·알림

- [ ] **I.1** Uptime Kuma에 모니터 등록:
  - 사용자 사이트(공개) — http(s) 200 체크
  - api 헬스체크 — http
  - PG/Redis — TCP
  - 외부: Nanobanana API, OpenAI Image API, Resend API
- [ ] **I.2** 알림 채널: 텔레그램 봇(또는 Slack 웹훅) 연결
- [ ] **I.3** Sentry 알림: high severity 1건이라도 발생 시 즉시 텔레그램
- [ ] **I.4** 디스크 사용량 80% 초과 시 알림 (cron + 스크립트)

---

## 3. 기술 결정사항 (Phase 0 한정)

### 3.1 결정 1 — 모노레포 vs 멀티레포

**선택**: **모노레포** (`vaultix` 단일 저장소, 내부에 `apps/api`, `apps/web`, `infra` 등)

| 옵션 | 장점 | 단점 |
|------|------|------|
| 모노레포 ⭐ | 컨텍스트 일치, PR 한 번에 통합 변경, CI 단순화 | 빌드 시간 ↑ (캐시로 완화) |
| 멀티레포 | 독립 배포 자유, repo별 권한 분리 | 1인 운영에 오버헤드 큼 |

근거: JH 1인 운영, 변경이 풀스택을 가로지르는 경우가 많음. 멀티레포의 장점은 팀 규모 5+ 이후 의미 있음.

### 3.2 결정 2 — Container Registry

**선택**: **GHCR (ghcr.io)**

근거: GitHub와 통합, 무료 (private도 무료 한도 충분), Actions 안에서 인증 자동.

### 3.3 결정 3 — Python 패키지 매니저

**선택**: **uv** (이미 VPS 설치됨)

근거: poetry 대비 10~100배 빠름, requirements 관리 호환, Docker 빌드 캐시 친화적.

### 3.4 결정 4 — Next.js 빌드 산출물

**선택**: **standalone output** (`output: 'standalone'`)

근거: Docker 이미지가 작아짐(node_modules 일부만 복사), 콜드 스타트 빠름.

### 3.5 결정 5 — Plausible vs Umami

**선택**: **Plausible 셀프호스트** (v0.3 결정 유지)

근거: ClickHouse 의존성 있어 약간 무겁지만, 쿼리 성능과 ClickHouse 기반 대시보드가 안정적. RAM 47GB라 부담 없음. Umami는 PG 단일이라 가벼우나 대용량에서 느려질 수 있음.

### 3.6 결정 6 — Telegram vs Slack vs Discord (알림)

**선택**: **Telegram 봇 1차** (BotFather로 5분에 생성). Slack 웹훅은 본업 회사 워크스페이스가 있으면 추가.

---

## 4. 코드/설정 골격

### 4.1 모노레포 디렉토리 구조

```
vaultix/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   └── deploy.yml
│   └── renovate.json
├── apps/
│   ├── api/                          # FastAPI
│   │   ├── pyproject.toml            # uv 관리
│   │   ├── uv.lock
│   │   ├── Dockerfile
│   │   ├── alembic.ini
│   │   ├── alembic/
│   │   │   └── versions/
│   │   └── src/
│   │       └── vaultix_api/
│   │           ├── __init__.py
│   │           ├── main.py
│   │           ├── settings.py
│   │           ├── deps.py            # DI
│   │           ├── db/
│   │           ├── models/
│   │           ├── schemas/
│   │           ├── routers/
│   │           │   ├── health.py
│   │           │   ├── auth.py        # Phase 1
│   │           │   ├── assets.py      # Phase 1
│   │           │   ├── downloads.py   # Phase 1
│   │           │   └── admin.py       # Phase 1
│   │           ├── services/
│   │           ├── workers/
│   │           │   └── celery_app.py  # Phase 1
│   │           └── adapters/          # 외부 시스템(Nanobanana, OpenAI Image, Comfy, Resend, DeepL)
│   └── web/                          # Next.js
│       ├── package.json
│       ├── pnpm-lock.yaml
│       ├── Dockerfile
│       ├── next.config.mjs
│       ├── tsconfig.json
│       ├── tailwind.config.ts
│       └── src/
│           └── app/
│               ├── layout.tsx
│               ├── page.tsx
│               ├── healthz/page.tsx
│               └── ...
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.override.yml   # 로컬 dev 전용 (gitignore 안 함)
│   ├── nginx/
│   │   ├── vaultix.conf
│   │   └── vaultix-admin.conf
│   ├── scripts/
│   │   ├── backup.sh
│   │   ├── restore.sh
│   │   └── healthcheck.sh
├── docs/                             # 산출물 사본 (선택)
├── .env.example
├── .gitignore
├── .editorconfig
├── LICENSE
└── README.md
```

### 4.2 docker-compose.yml (Phase 0 골격)

```yaml
# infra/docker-compose.yml
name: vaultix

networks:
  internal:
    name: vaultix_internal
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16

volumes:
  pg_data:
    driver: local
    driver_opts:
      type: none
      device: /var/lib/vaultix/postgres
      o: bind
  redis_data:
    driver: local
    driver_opts:
      type: none
      device: /var/lib/vaultix/redis
      o: bind
services:
  postgres:
    image: postgres:17-alpine
    container_name: vaultix-postgres
    restart: unless-stopped
    networks: [internal]
    environment:
      POSTGRES_DB: vaultix
      POSTGRES_USER: ${PG_USER}
      POSTGRES_PASSWORD: ${PG_PASSWORD}
      TZ: Asia/Seoul
    volumes:
      - pg_data:/var/lib/postgresql/data
    ports:
      - "127.0.0.1:5440:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${PG_USER} -d vaultix"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: vaultix-redis
    restart: unless-stopped
    networks: [internal]
    command: ["redis-server", "--requirepass", "${REDIS_PASSWORD}", "--appendonly", "yes"]
    volumes:
      - redis_data:/data
    ports:
      - "127.0.0.1:6380:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  api:
    image: ghcr.io/${GH_OWNER}/vaultix-api:${IMAGE_TAG:-latest}
    container_name: vaultix-api
    restart: unless-stopped
    networks: [internal]
    depends_on:
      postgres: { condition: service_healthy }
      redis:    { condition: service_healthy }
    environment:
      DATABASE_URL: postgresql+psycopg://${PG_USER}:${PG_PASSWORD}@postgres:5432/vaultix
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      SENTRY_DSN: ${SENTRY_DSN_API}
      ENV: production
      TZ: Asia/Seoul
    ports:
      - "127.0.0.1:8302:8000"
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 5s
      retries: 3

  web:
    image: ghcr.io/${GH_OWNER}/vaultix-web:${IMAGE_TAG:-latest}
    container_name: vaultix-web
    restart: unless-stopped
    networks: [internal]
    depends_on: [api]
    environment:
      NEXT_PUBLIC_API_BASE: https://vaultix.example.com/api
      NEXT_PUBLIC_PLAUSIBLE_DOMAIN: vaultix.example.com
      SENTRY_DSN: ${SENTRY_DSN_WEB}
      TZ: Asia/Seoul
    ports:
      - "127.0.0.1:8301:3000"
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:3000/healthz"]
      interval: 30s
      timeout: 5s
      retries: 3

  # Plausible (Phase 0에 포함)
  plausible-db:
    image: postgres:16-alpine
    container_name: vaultix-plausible-db
    restart: unless-stopped
    networks: [internal]
    environment:
      POSTGRES_DB: plausible_db
      POSTGRES_USER: plausible
      POSTGRES_PASSWORD: ${PLAUSIBLE_DB_PASSWORD}
      TZ: Asia/Seoul
    volumes:
      - /var/lib/vaultix/plausible/db:/var/lib/postgresql/data

  plausible-events-db:
    image: clickhouse/clickhouse-server:24.3-alpine
    container_name: vaultix-plausible-clickhouse
    restart: unless-stopped
    networks: [internal]
    volumes:
      - /var/lib/vaultix/plausible/clickhouse:/var/lib/clickhouse
      - ./plausible/clickhouse-config.xml:/etc/clickhouse-server/config.d/logging.xml:ro
    ulimits:
      nofile: { soft: 262144, hard: 262144 }

  plausible:
    image: ghcr.io/plausible/community-edition:v3.0.1
    container_name: vaultix-plausible
    restart: unless-stopped
    networks: [internal]
    depends_on: [plausible-db, plausible-events-db]
    environment:
      BASE_URL: https://plausible.vaultix.example.com
      SECRET_KEY_BASE: ${PLAUSIBLE_SECRET_KEY}
      TOTP_VAULT_KEY: ${PLAUSIBLE_TOTP_KEY}
      DATABASE_URL: postgres://plausible:${PLAUSIBLE_DB_PASSWORD}@plausible-db:5432/plausible_db
      CLICKHOUSE_DATABASE_URL: http://plausible-events-db:8123/plausible_events_db
      TZ: Asia/Seoul
    ports:
      - "127.0.0.1:8303:8000"
    command: sh -c "/entrypoint.sh db createdb && /entrypoint.sh db migrate && /entrypoint.sh run"

  uptime-kuma:
    image: louislam/uptime-kuma:1
    container_name: vaultix-uptime-kuma
    restart: unless-stopped
    networks: [internal]
    volumes:
      - /var/lib/vaultix/uptime-kuma:/app/data
    ports:
      - "127.0.0.1:8305:3001"
```

> **참고**: 위는 Phase 0 골격. Phase 1에서 Celery 워커, Listmonk, MinIO(또는 R2) 마이그레이션이 추가됨.

### 4.3 nginx 설정 (시스템 nginx에 추가)

```nginx
# /etc/nginx/sites-available/vaultix.conf
# 공개 사이트 (사용자용)

upstream vaultix_web { server 127.0.0.1:8301; }
upstream vaultix_api { server 127.0.0.1:8302; }

server {
    listen 80;
    listen [::]:80;
    server_name vaultix.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name vaultix.example.com;

    ssl_certificate     /etc/letsencrypt/live/vaultix.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/vaultix.example.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;

    # 기본 보안 헤더
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # 어드민 — Tailscale 대역만 허용
    location /admin/ {
        allow 100.64.0.0/10;
        deny all;
        proxy_pass http://vaultix_web;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    # API — 공개 (회원가입·자산 조회 등). 어드민 API는 /api/admin/* 별도 ALLOW
    location /api/admin/ {
        allow 100.64.0.0/10;
        deny all;
        proxy_pass http://vaultix_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    location /api/ {
        proxy_pass http://vaultix_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        client_max_body_size 25m;
    }

    # 정적 자산(추후 Phase 1+) — 다운로드는 signed URL을 통해서만
    location /assets/ {
        internal;  # signed URL 검증 후에만 X-Accel-Redirect
        alias /var/lib/vaultix/assets/;
    }

    # 그 외 → Next.js
    location / {
        proxy_pass http://vaultix_web;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```nginx
# /etc/nginx/sites-available/vaultix-admin.conf
# Tailscale 전용 — Plausible, Uptime Kuma

server {
    listen 443 ssl http2;
    server_name plausible.vaultix.example.com;

    # Tailscale 대역만
    allow 100.64.0.0/10;
    deny all;

    ssl_certificate     /etc/letsencrypt/live/plausible.vaultix.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/plausible.vaultix.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8303;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}

server {
    listen 443 ssl http2;
    server_name uptime.vaultix.example.com;

    allow 100.64.0.0/10;
    deny all;

    ssl_certificate     /etc/letsencrypt/live/uptime.vaultix.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/uptime.vaultix.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8305;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 4.4 FastAPI 골격 (Phase 0 — 헬스체크만)

```python
# apps/api/src/vaultix_api/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from vaultix_api.settings import settings

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.env,
        traces_sample_rate=0.1,
        integrations=[FastApiIntegration()],
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: DB 연결 검증, Redis ping
    yield
    # shutdown

app = FastAPI(title="vaultix API", lifespan=lifespan)

@app.get("/healthz")
async def healthz():
    return {"status": "ok", "env": settings.env}
```

```python
# apps/api/src/vaultix_api/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    env: str = "development"
    database_url: str
    redis_url: str
    sentry_dsn: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
```

```toml
# apps/api/pyproject.toml
[project]
name = "vaultix-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.30",
  "pydantic>=2.9",
  "pydantic-settings>=2.5",
  "sqlalchemy>=2.0",
  "alembic>=1.13",
  "psycopg[binary]>=3.2",
  "redis>=5.0",
  "celery>=5.4",
  "sentry-sdk[fastapi]>=2.14",
  "httpx>=0.27",
  "python-jose[cryptography]>=3.3",
  "passlib[argon2]>=1.7",
]

[dependency-groups]
dev = [
  "pytest>=8",
  "pytest-asyncio>=0.24",
  "ruff>=0.6",
  "mypy>=1.11",
]
```

### 4.5 Next.js 골격 (Phase 0 — 헬스체크만)

```ts
// apps/web/src/app/healthz/page.tsx
export default function Healthz() {
  return <main>OK</main>;
}
```

```js
// apps/web/next.config.mjs
import { withSentryConfig } from "@sentry/nextjs";

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  experimental: { typedRoutes: true },
};

export default withSentryConfig(nextConfig, { silent: true });
```

### 4.6 GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push: { branches: [main] }
  pull_request:

jobs:
  api:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: apps/api } }
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: uv run ruff check
      - run: uv run pytest -q

  web:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: apps/web } }
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with: { version: 9 }
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: pnpm, cache-dependency-path: apps/web/pnpm-lock.yaml }
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint
      - run: pnpm build

  build-images:
    needs: [api, web]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v6
        with:
          context: ./apps/api
          push: true
          tags: |
            ghcr.io/${{ github.repository_owner }}/vaultix-api:${{ github.sha }}
            ghcr.io/${{ github.repository_owner }}/vaultix-api:latest
      - uses: docker/build-push-action@v6
        with:
          context: ./apps/web
          push: true
          tags: |
            ghcr.io/${{ github.repository_owner }}/vaultix-web:${{ github.sha }}
            ghcr.io/${{ github.repository_owner }}/vaultix-web:latest
```

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
    branches: [main]

jobs:
  deploy:
    if: github.event.workflow_run.conclusion == 'success'
    runs-on: [self-hosted, main-hub]
    steps:
      - uses: actions/checkout@v4
      - name: Pull and restart
        run: |
          cd /opt/vaultix
          git fetch --all && git reset --hard origin/main
          export IMAGE_TAG=${{ github.sha }}
          docker compose -f infra/docker-compose.yml --env-file /opt/vaultix/.env pull
          docker compose -f infra/docker-compose.yml --env-file /opt/vaultix/.env up -d
      - name: Healthcheck
        run: |
          for i in {1..30}; do
            curl -fsS http://127.0.0.1:8302/healthz && exit 0
            sleep 2
          done
          exit 1
```

### 4.7 백업 스크립트

```bash
#!/usr/bin/env bash
# infra/scripts/backup.sh
set -euo pipefail

DATE=$(date +%Y%m%d-%H%M)
BACKUP_DIR=/var/lib/vaultix/backup
GDRIVE_DIR=/mnt/gdrive/vaultix-backup

mkdir -p "$BACKUP_DIR"

# PostgreSQL dump
docker exec vaultix-postgres pg_dump -U "$PG_USER" -d vaultix --format=custom \
  --compress=9 --file=/tmp/vaultix-${DATE}.dump
docker cp vaultix-postgres:/tmp/vaultix-${DATE}.dump "$BACKUP_DIR/"
docker exec vaultix-postgres rm /tmp/vaultix-${DATE}.dump

# Restic 증분 백업 (자산 + DB dump)
restic -r "$GDRIVE_DIR" backup \
  /var/lib/vaultix/assets \
  "$BACKUP_DIR" \
  --tag daily

# 30일 이상 dump는 로컬에서 정리 (gdrive에는 restic이 보존정책 관리)
find "$BACKUP_DIR" -name "vaultix-*.dump" -mtime +30 -delete

# Restic 보존 정책: 일 7개, 주 4개, 월 6개
restic -r "$GDRIVE_DIR" forget \
  --keep-daily 7 --keep-weekly 4 --keep-monthly 6 \
  --prune
```

### 4.8 .env.example

```dotenv
# .env.example (실제 .env는 main-hub /opt/vaultix/.env 에 수동 배치, gitignore)
ENV=production
GH_OWNER=jh-or-org

# PostgreSQL
PG_USER=vaultix
PG_PASSWORD=change-me-strong

# Redis
REDIS_PASSWORD=change-me-strong

# Sentry
SENTRY_DSN_API=
SENTRY_DSN_WEB=

# Plausible
PLAUSIBLE_DB_PASSWORD=change-me
PLAUSIBLE_SECRET_KEY=  # mix_gen_secret 64
PLAUSIBLE_TOTP_KEY=    # 32bytes base64

# Restic
RESTIC_PASSWORD=change-me-strong

# Phase 1+에서 추가됨
# RESEND_API_KEY=
# NANOBANANA_API_KEY=
# NANOBANANA_BASE_URL=
# OPENAI_API_KEY=
# OPENAI_IMAGE_MODEL=gpt-image-2
# ANTHROPIC_API_KEY=
# GOOGLE_AI_API_KEY=
# ZAI_API_KEY=
# DEEPL_API_KEY=
# COMFY_HOST=http://100.x.x.x:8188
```

---

## 5. 테스트 계획

### 5.1 단위 테스트 (Phase 0 한정)

| 대상 | 테스트 항목 |
|------|------------|
| api `/healthz` | 200 응답, JSON 형식 |
| settings 로드 | 필수 환경변수 누락 시 startup 실패 |
| Sentry 통합 | 의도적 raise → Sentry 이벤트 도착 (수동 검증 1회) |
| Alembic | `upgrade head` → `downgrade base` → `upgrade head` 사이클 OK |

### 5.2 통합 테스트

| 시나리오 | 기대 |
|---------|------|
| `docker compose up -d` 후 60초 내 모든 healthcheck `healthy` | OK |
| Tailscale 대역 외 IP에서 `/admin/` 접속 | 403 |
| Tailscale 대역 내 IP에서 `/admin/` 접속 | 200 |
| `git push origin main` → 5분 내 새 이미지 배포 + `/healthz` OK | OK |
| 의도적 빌드 실패 PR | CI 실패, 배포 미진행 |
| pg_dump → restic → gdrive 도착 | OK |
| restore.sh로 별도 임시 DB 복원 → 데이터 일치 | OK |
| 데스크탑 ComfyUI에 워크플로우 POST → 이미지 다운로드 | OK |
| 데스크탑 끄고 main-hub에서 ComfyUI 호출 | 타임아웃 후 실패 응답 (Phase 1에서 폴백 로직 추가) |

### 5.3 부하·안정성 (Phase 0은 가벼운 수준)

- Apache Bench 또는 `wrk`로 `/healthz`에 100 RPS × 60초 → 에러율 0%
- 7일간 Uptime Kuma 가동, 다운타임 0건 확인

---

## 6. 리스크 & 대응

| 리스크 | 가능성 | 영향 | 대응 |
|--------|:---:|:---:|------|
| 시스템 nginx 설정 실수로 기존 25개 컨테이너 다운 | 中 | 高 | `nginx -t`로 syntax 검증 후 reload, 변경 전 `cp -a /etc/nginx /etc/nginx.bak.$(date)` |
| ufw 규칙 편집 중 SSH 차단 | 中 | 高 | Tailscale로 SSH 백업 경로 확보 (이미 있음). 변경 전 `ufw status numbered` 백업 |
| GHCR 무료 한도 초과 | 低 | 中 | Phase 0에서 이미지 태그 정리 정책 도입 (latest + 최근 5개 SHA만 유지) |
| Plausible ClickHouse 디스크 폭증 | 低 | 中 | 보존 정책 90일, 디스크 알림 80% |
| Sentry 무료 한도(이벤트/월) 초과 | 中 | 低 | sample rate 조정, traces_sample_rate 0.1 시작 |
| 데스크탑 ↔ Tailscale 불안정 | 中 | 中 | Phase 0 PoC 단계에서 라운드트립 5분 폴링으로 안정성 측정. 폴백 외부 API는 Phase 1에서 구현 |
| 빌드 시간 길어짐 (Next.js + 의존성) | 中 | 低 | pnpm 캐시, Docker BuildKit 캐시 마운트 사용 |
| self-hosted runner가 main-hub 자원 잡아먹음 | 中 | 中 | runner CPU/메모리 제한 (systemd `MemoryMax=4G CPUQuota=200%`) |
| Renovate가 너무 많은 PR 생성 | 中 | 低 | grouping rule + auto-merge 룰 설정 |

---

## 7. Phase 1 진입 조건

> 다음을 **모두** 만족해야 Phase 1 시작.

- [ ] §1.2 완료 조건 모든 체크박스 ✅
- [ ] 배포 자동화 검증: 의도적으로 web에 1줄 변경 + push → 5분 내 운영 반영 확인 (3회 연속 성공)
- [ ] 백업·복원 1회 성공
- [ ] 모니터링 알림 1회 수동 트리거 검증
- [ ] 데스크탑 ComfyUI 라운드트립 PoC 성공 + 라운드트립 시간 베이스라인 기록
- [ ] 7일간 무중단 운영 확인
- [ ] Phase 1 입력 기획서 4개 (A1, A2, A3, 02_Phase1) 작성 완료 — 코워크에서 묶음 2로 받음

---

## 8. 다음 액션 (이 문서 외)

1. JH가 본 문서 §1.2 완료 조건 + §2 WBS를 정독 후 의견 → 필요 시 갱신
2. JH가 §2.1 사전 준비 항목부터 직접 착수
3. 막히는 항목은 코워크에서 "Phase 0 §2.X에서 막힘" 형식으로 질문


