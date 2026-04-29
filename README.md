# Vaultix

Vaultix is an AI productivity asset hub project.

This repository contains the implementation-ready planning package and the first Sprint 0
monorepo baseline for the MVP:

- Phase 0 infrastructure setup
- Phase 1 Korean image asset MVP
- Post-MVP release train
- LLM/image routing policy
- Data model, API spec, operations runbook, and design system
- FastAPI API skeleton under `apps/api`
- Next.js web skeleton under `apps/web`
- Docker Compose and nginx templates under `infra`

Start here:

1. `구현시작_README.md`
2. `기획서/00_IMPLEMENTATION_SPEC_v0.4.md`
3. `기획서/00_확정사항_레지스트리.md`
4. `기획서/A7_LLM_라우팅_정책.md`

Final project name: **Vaultix**

GitHub repository: `https://github.com/naral3221-dotcom/vaultix.git`

Important implementation rule:

- Do not create an Ollama container for the MVP.
- Local GGUF models under `C:\AI\llm` are optional/experimental resources.
- MVP generation uses Nanobanana API -> OpenAI `gpt-image-2` -> ComfyUI special workflow.

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

The default local ports follow the Phase 0 plan:

- Web: `127.0.0.1:8301`
- API: `127.0.0.1:8302`
- PostgreSQL: `127.0.0.1:5440`
- Redis: `127.0.0.1:6380`
