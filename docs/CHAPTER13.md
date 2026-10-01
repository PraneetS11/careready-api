# Chapter 13: middleware and request policies

Request logging records method, route template, HTTP status and elapsed milliseconds. It does not record headers, bodies, query strings, client addresses or concrete path parameters. Unknown routes use `<unmatched>`, so arbitrary token-bearing URLs are not echoed. The raw Uvicorn access logger is disabled in favor of this safe logger. Unhandled exceptions still propagate; the middleware records status 500 without swallowing them or logging their text.

`CORS_ORIGINS` and `ALLOWED_HOSTS` accept JSON lists in the existing Settings environment configuration. Development defaults allow browser origins `http://localhost:3000` and `http://localhost:5173`, and hostnames `localhost` and `127.0.0.1`. Test mode also allows `testserver`. An origin includes scheme, host and port; a trusted host is a hostname. CORS controls browser access and does not replace authentication. Configure real deployment origins and hosts deliberately before deployment.

Verified 2026-10-01: full regression suite passes (49 tests), along with lint/import checks. Middleware tests cover successful and handled 404 responses, exceptions, allowed/unlisted origins, preflight, invalid hosts, docs, and omission of secrets from logs. Live API checks confirm these policies are actually registered and protected endpoints still require tokens. No database migration was needed.

Chapter 12 commit: `7403cef2001fa0f4c4cb16f285c21ecad7ab13a3`; its GitHub checks passed.
