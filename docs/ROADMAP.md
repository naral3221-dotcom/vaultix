# Vaultix Development Roadmap

Last updated: 2026-05-01

## Phase Overview

| Phase | Status | Progress | Focus |
| --- | --- | ---: | --- |
| Phase 0 | Done | 100% | VPS, Docker Compose, PostgreSQL, Redis, API/Web baseline, Tailnet nginx |
| Phase 1 | Done | 100% | Public catalog, account flow, download links, Resend/Turnstile abuse checks |
| Phase 2 | Active | 90% | Admin operation, reports, audit logs, roadmap visibility, Google OAuth, generation queue MVP |
| Phase 3 | Next | 10% | Nanobanana -> OpenAI gpt-image-2 generation pipeline |
| Phase 4 | Later | 0% | SEO, analytics, monitoring, backups |

## Current Phase

Phase 2 관리자 운영 is active.

Completed:
- Admin role and `ADMIN_EMAILS`
- Google OAuth login connected to the existing session cookie
- Admin access guidance
- Asset review and publish status changes
- Report resolution and audit logs
- Asset generation request queue MVP

In progress:
- Admin UX cleanup

Next:
- AI worker queue connection

## Next Major Milestone

Finish the remaining admin UX cleanup.
After that, wire the AI generation pipeline: Nanobanana first, OpenAI `gpt-image-2` fallback, Celery queue, prompt templates, and thumbnail/WebP processing.
