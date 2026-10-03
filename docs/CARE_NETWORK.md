# Care network increment

CareReady now supports requester, provider and agency accounts through `/api/v1/network/register`. Existing chapter endpoints remain compatible. All operational routes require verified email. An agency approves only its own verified providers; approval represents the agency's manual review, not automated credential verification.

Requesters submit one-time or weekly visits (1–12 occurrences). An agency publishes its own requests. Providers see only open, future visits for their agency, service types and experience level, excluding schedule conflicts with a 30-minute travel buffer. Acceptance locks the provider and visit records to prevent duplicate and overlapping assignments. City centroids appear on the public job view; recipient, address, notes and requester identity are withheld until assignment. Agency and requester views are ownership-scoped.

Gender, language, communication style, smoke-free preferences and pets are fit information, not automatic employment exclusions. Experience is four simple levels. Providers declare services/languages; agencies must review suitability before approval. Recurrence preserves the local city timezone across daylight saving and rejects nonexistent local times. Each occurrence is a separate visit and is cancelled independently.

Agency equipment inventory records asset codes and available/in-use/maintenance states. Equipment reservation, payments, clinical charting, formal credential validation, recurring-series editing and automatic dispatch are not implemented. This is a local fictional-data demonstration.

Verification: `make lint`; `RUN_INTEGRATION=1 make test` (65 passing); `.venv/bin/python scripts/verify_network.py` against `compose.test.yaml` confirms isolation, preferences, recurrence, privacy, acceptance races and equipment ownership. The latter runs in CI too.

## Low-priority follow-ups

HIPAA readiness is a future organizational/deployment workstream, not a current compliance claim. Use fictional information only. Production work would require a jurisdiction-specific privacy/security review, operating procedures, access/audit review and appropriate service agreements.

Freelance companionship is a future extension. Entry-level companionship currently works through an agency-approved provider. Background-check status, reviewer/date/evidence, expiry and service restrictions need explicit modeling before independent onboarding. A background check must not automatically authorize clinical services.

## Local frontend

Run `docker compose --env-file .env.demo -p careready-demo -f compose.demo.yaml up -d --build --wait`, then `.venv/bin/python scripts/seed_network_demo.py` for fictional examples. Open http://127.0.0.1:8080; mailbox http://127.0.0.1:8029. The seed script never targets another host and will not duplicate existing example visits.

Demo-only accounts: `requester@demo.careready.example`, `provider@demo.careready.example`, `agency@demo.careready.example`. All use `CareReady-demo-2026!`. These intentionally public demo credentials must never be used with real information or a public deployment. Normal signup creates unverified accounts; the seed helper confirms its fictional accounts through actual sandbox emails.

Frontend: React 19, TypeScript, Vite, TanStack Query, React Router, Tailwind CSS, Motion, Three.js/React Three Fiber, Vitest, Testing Library and ESLint. Tokens stay in memory; reloading requires signing in again. Refresh and logout use the existing backend token flow. Frontend email links lead to verification/reset screens. Nginx suppresses URL access logs so email-link tokens are not logged.

Globe coastlines are bundled from Natural Earth: https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_land.geojson . No external map token or runtime map service is required. Only actual eligible jobs become points, grouped by city. Orbit animation can be paused and respects reduced-motion settings; an equivalent job list remains available.

Frontend commands: `npm ci --prefix frontend`, `npm run lint --prefix frontend`, `npm run test --prefix frontend`, `npm run build --prefix frontend`. Development: `npm run dev --prefix frontend` proxies the local API on port 8009.
