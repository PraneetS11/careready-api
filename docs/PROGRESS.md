# CareReady chapter progress

One assignment after completing each matching Bookly chapter. This chapter edition supersedes C01-C29 and the small P/E-checkpoint draft. Prior tracker: archive/guide-v1/PROGRESS.md. No chapter is marked complete automatically.

Record real date and proof before the chapter commit; add its SHA in the next documentation update.

| Done | Chapter | Video end | Assignment | Actual date | Feature SHA | Success evidence / blocker |
|---|---|---|---|---|---|---|
| [ ] | CH01 | 0:07:30 | Installation and project setup | | | |
| [ ] | CH02 | 0:49:43 | Creating a simple web server | | | |
| [ ] | CH03 | 1:23:37 | Building a CRUD REST API | | | |
| [ ] | CH04 | 1:38:22 | Large project structure using routers | | | |
| [x] | CH05 | 2:29:48 | Databases with SQLModel | 2026-09-30 | 4b95de6 | Local PostgreSQL/Redis healthy; readiness 200 on two startups; one site table with UUID primary key and all five required columns; clean shutdown twice; 8 tests pass. See verification below. |
| [x] | CH06 | 3:33:35 | Finishing the database CRUD | 2026-09-30 | | PostgreSQL CRUD verified over HTTP; create/update survive separate API process restarts; filter, 201/204/404/422 checks pass; 15 tests and full lint pass. |
| [ ] | CH07 | 3:59:57 | Creating the user authentication model | | | |
| [ ] | CH08 | 4:42:57 | User account creation | | | |
| [ ] | CH09 | 6:07:39 | JWT authentication | | | |
| [ ] | CH10 | 6:39:24 | Role-based access control | | | |
| [ ] | CH11 | 7:59:58 | Model and schema relationships | | | |
| [ ] | CH12 | 8:33:25 | Error handling | | | |
| [ ] | CH13 | 9:05:04 | Middleware | | | |
| [ ] | CH14 | 10:40:38 | Email support | | | |
| [ ] | CH15 | 11:23:48 | Background processing | | | |
| [ ] | CH16 | 11:36:02 | API documentation | | | |
| [ ] | CH17 | 12:09:17 | Testing: pytest, mocks and Schemathesis | | | |
| [ ] | CH18 | 12:52:54 | Deployment | | | |

## CH05 verification

- Applied to the existing development setup; Settings, `.env.example`, Compose,
  session dependency and Chapter 4 route/data files required no changes.
- Two real application lifespan runs against local PostgreSQL and Redis each
  returned `/health/ready` 200 with both dependency checks `ok`, followed by clean
  shutdown. Inspected the database after each startup: exactly one `site` table,
  UUID `id` primary key, and non-null `id`, `name`, `city`, `timezone`, `active`.
- `python -m compileall -q app` passed using the project virtual environment.
- `make test`: 8 passed, including generated UUID/schema checks and the retained
  in-memory create/read/filter/update/delete behavior. The existing Starlette
  TestClient/httpx deprecation warning remains.
- Follow-up formatting cleanup in `app/api/sites.py` and `app/api/site_data.py`
  resolves the GitHub Actions import-spacing failure. Full-project `make lint`
  now passes (25 files formatted), and `make test` still reports 8 passed.
  The cleanup changes whitespace only; Chapter 4 route behavior is preserved.
- HTTP site CRUD still uses memory and integer ids until CH06. Table initialization
  runs only in development; tests explicitly use the test environment.
- Implementation committed and pushed as `4b95de6`; recorded in this follow-up.

## CH06 verification

- Reused the existing engine, SQLAlchemy AsyncSession and per-request dependency.
  SiteService owns database operations and write rollback; routes expose SiteRead.
  Removed the unused in-memory site_data module.
- Live verification used the configured local PostgreSQL and Redis services and
  temporary API processes. Initial site list was empty; readiness returned 200.
- Created a unique test site (201), fetched and listed its UUID, stopped the API
  process and started a new one, and retrieved the same record. Patched active to
  false, restarted the API process again, and verified the update persisted.
- SQL active=true/false filters excluded/included that UUID correctly. Deleted
  the test site (204 with empty body); subsequent GET and DELETE returned 404.
  Valid unknown UUIDs returned 404 for GET/PATCH/DELETE; malformed UUIDs and
  invalid create/update bodies returned 422. All test-created records were removed.
- `make lint`, `make test` (15 passed), and compileall passed. Tests cover response
  contracts, UUID/body validation, SQL filters and rollback for failed writes.
- Feature SHA is intentionally blank until a later documentation update.
