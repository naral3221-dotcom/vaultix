# Vaultix

Vaultix is an AI productivity asset hub project.

This repository currently contains the implementation-ready planning package for the MVP:

- Phase 0 infrastructure setup
- Phase 1 Korean image asset MVP
- Post-MVP release train
- LLM/image routing policy
- Data model, API spec, operations runbook, and design system

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
