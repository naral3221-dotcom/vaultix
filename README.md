# Vaultix

> AI 생산성 에셋 허브 — 한국어 이미지 자산 카탈로그 + 자동 생성 파이프라인.

- **Version**: `0.1.0` (apps/api · apps/web 공통, 모노레포 루트 `VERSION` 참조)
- **Current phase**: Phase 3 (Active, 85%) — image supply pipeline
- **Status**: Pre-MVP. Phase 0/1/2 완료, Phase 3 진행 중.

## Repository

| Remote | URL | 용도 |
|---|---|---|
| **`origin`** (primary) | `http://100.116.156.37:9006/jh97/vaultix.git` | **Vault** — self-hosted Gitea (Tailscale 전용). 모든 커밋·푸시의 디폴트. |
| `github` (backup) | `git@github.com:naral3221-dotcom/vaultix.git` | 비활성 백업. 거의 사용하지 않음. 명시 요청 시에만 `git push github main`. |

Vault 웹 UI: `http://100.116.156.37:9006/jh97/vaultix` (PC 에서는 Tailscale 켠 상태로 접근)

## What's in this repo

- `apps/api` — FastAPI service (Python 3.12+, uv, SQLAlchemy 2, Alembic)
- `apps/web` — Next.js 14 web (App Router, TypeScript, pnpm@10.33.2)
- `infra` — Docker Compose, nginx templates, healthcheck scripts
- `기획서/` — 23개 구현 기준 문서 (한국어)
- `docs/ROADMAP.md` — Phase 상태 단일 진실 공급원
- `.agent/` — AI 에이전트 메모리 인프라 (state · log · wiki)

## Start here

먼저 읽을 문서 (우선순위 순):

1. `구현시작_README.md`
2. `기획서/00_IMPLEMENTATION_SPEC_v0.4.md` — 구현 기준 단일본 (충돌 시 우선)
3. `기획서/00_확정사항_레지스트리.md`
4. `기획서/A7_LLM_라우팅_정책.md`
5. `docs/ROADMAP.md` — 현재 Phase 상태
6. `.agent/wiki/README.md` — AI 에이전트용 컨텍스트 인덱스

## Implementation rules

- Do not create an Ollama container for the MVP.
- Local GGUF models under `C:\AI\llm` are optional/experimental resources.
- MVP generation: **Nanobanana API → OpenAI `gpt-image-2` → ComfyUI** special workflow.
- All LLM calls go through the **OpenClaw Gateway** (no direct `anthropic` / `openai` / `google-genai` SDK imports).

## Local Development

API:

```bash
cd apps/api
VAULTIX_ENV=test uv run pytest -q
uv run uvicorn vaultix_api.main:app --reload
```

Web:

```bash
cd apps/web
corepack pnpm install
corepack pnpm test -- --run
corepack pnpm dev
```

Compose validation:

```bash
docker compose -f infra/docker-compose.yml config
```

Local Compose stack:

```bash
docker compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml up -d postgres redis
cd apps/api
DATABASE_URL=postgresql+psycopg://vaultix:change-me@localhost:5440/vaultix uv run alembic upgrade head
cd ../..
docker compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml up -d api web
infra/scripts/healthcheck.sh
```

Default local ports (Phase 0 plan):

- Web: `127.0.0.1:8301`
- API: `127.0.0.1:8302`
- PostgreSQL: `127.0.0.1:5440`
- Redis: `127.0.0.1:6380`

## Versioning

- 루트 `VERSION` 파일이 단일 진실 공급원.
- `apps/api/pyproject.toml` 과 `apps/web/package.json` 의 `version` 은 이 값과 동기화.
- MVP (Phase 0 + Phase 1) 완료 시 `1.0.0` 으로 bump 예정. 그 전까지 `0.x.y`.

## License

`기획서/A5_라이선스_본문_초안.md` 의 한·영 본문이 라이선스 원본. 발행 자산 단위 라이선스는 자산 메타데이터에 포함.
