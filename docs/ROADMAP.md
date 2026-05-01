# Vaultix Development Roadmap

Last updated: 2026-05-01

## Phase Overview

| Phase | Status | Progress | Focus |
| --- | --- | ---: | --- |
| Phase 0 | Done | 100% | VPS, Docker Compose, PostgreSQL, Redis, API/Web baseline, Tailnet nginx |
| Phase 1 | Done | 100% | Public catalog, account flow, download links, Resend/Turnstile abuse checks |
| Phase 2 | Done | 100% | Admin operation, reports, audit logs, roadmap visibility, Google OAuth, generation queue MVP |
| Phase 3 | Active | 55% | Image supply pipeline, admin metadata editing, OpenAI GPT Image provider path |
| Phase 4 | Later | 0% | SEO, analytics, monitoring, backups |

## Current Phase

Phase 3 이미지 공급 파이프라인 is active.

Completed:
- Admin role and `ADMIN_EMAILS`
- Google OAuth login connected to the existing session cookie
- Admin access guidance
- Asset review and publish status changes
- Report resolution and audit logs
- Asset generation request queue MVP
- Generation request worker bridge that creates inbox assets
- OpenAI GPT Image provider call path
- Admin asset metadata editing before publish

In progress:
- Production API key setup and generated asset storage

Next:
- Bulk image import/registration
- Prompt templates and result review
- Thumbnail/WebP processing

## Next Major Milestone

Set `OPENAI_API_KEY` in the VPS environment and confirm generated file storage.
After that, add a bulk image import/registration path and thumbnail/WebP processing so Vaultix can grow the curated reference library quickly.
