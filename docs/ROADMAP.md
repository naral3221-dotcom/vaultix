# Vaultix Development Roadmap

Last updated: 2026-05-01

## Phase Overview

| Phase | Status | Progress | Focus |
| --- | --- | ---: | --- |
| Phase 0 | Done | 100% | VPS, Docker Compose, PostgreSQL, Redis, API/Web baseline, Tailnet nginx |
| Phase 1 | Done | 100% | Public catalog, account flow, download links, Resend/Turnstile abuse checks |
| Phase 2 | Done | 100% | Admin operation, reports, audit logs, roadmap visibility, Google OAuth, generation queue MVP |
| Phase 3 | Active | 25% | Generation queue worker bridge, provider integration next |
| Phase 4 | Later | 0% | SEO, analytics, monitoring, backups |

## Current Phase

Phase 3 AI 생성 파이프라인 is active.

Completed:
- Admin role and `ADMIN_EMAILS`
- Google OAuth login connected to the existing session cookie
- Admin access guidance
- Asset review and publish status changes
- Report resolution and audit logs
- Asset generation request queue MVP
- Generation request worker bridge that creates inbox assets

In progress:
- Real Nanobanana/OpenAI provider call path

Next:
- Celery worker separation
- Prompt templates and result review
- Thumbnail/WebP processing

## Next Major Milestone

Wire real provider calls: Nanobanana first, OpenAI `gpt-image-2` fallback.
After that, split the current on-demand worker path into a Celery queue and add prompt templates plus thumbnail/WebP processing.
