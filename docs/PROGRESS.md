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
| [x] | CH06 | 3:33:35 | Finishing the database CRUD | 2026-09-30 | 2193bf4 | PostgreSQL CRUD verified over HTTP; create/update survive separate API process restarts; filter, 201/204/404/422 checks pass; 15 tests and full lint pass. |
| [x] | CH07 | 3:59:57 | Creating the user authentication model | 2026-09-30 | 5051fd4 | Empty careready_ch07 upgraded to c8af9d233c2f; repeat upgrade and schema check passed; safe UserRead and unique email verified; site create/list/restart passed without startup DDL; original practice rows preserved; 15 tests and lint pass. |
| [x] | CH08 | 4:42:57 | User account creation | 2026-10-01 | | Signup 201 with safe fields; normalized duplicate 409; invalid input 422; Argon2 correct/wrong verification; concurrent uniqueness conflict rolls back; 15 tests, lint and dependency check pass. |
| [x] | CH09 | 6:07:39 | JWT authentication | 2026-10-01 | | Login, protected CRUD, refresh and Redis revocation verified live; restart retains revocation; 32 tests and full lint pass. |
| [x] | CH10 | 6:39:24 | Role-based access control | 2026-10-01 | | 37 tests and lint pass; migration/no drift; live role enforcement, current account and deactivation verified. |
| [x] | CH11 | 7:59:58 | Model and schema relationships | 2026-10-01 | | 43 tests/lint; migration no drift; live creator, note isolation, shared tags/idempotence and restart checks pass. |
| [x] | CH12 | 8:33:25 | Error handling | 2026-10-01 | | 46 tests/lint; stable site_not_found on reads, edits, deletes and note access; live relationship regressions pass. |
| [x] | CH13 | 9:05:04 | Middleware | 2026-10-01 | | 49 tests/full lint; live safe logs, CORS/preflight, invalid hosts, docs and authentication checks pass. |
| [x] | CH14 | 10:40:38 | Email support | 2026-10-01 | | 52 tests/lint; local SMTP verification/recovery and restart checks pass. See CHAPTER14.md. |
| [x] | CH15 | 11:23:48 | Background processing | 2026-10-01 | | 54 tests/lint; real BackgroundTasks timing, stopped-worker queue recovery, Flower success/failure and queued auth mail verified. |
| [x] | CH16 | 11:36:02 | API documentation | 2026-10-01 | | 55 tests/lint; OpenAPI examples, bearer security and errors verified; live docs pass; practice routes removed and README scope corrected. |
| [x] | CH17 | 12:09:17 | Testing: pytest, mocks and Schemathesis | 2026-10-01 | | 58 tests twice/reversed order; isolated PostgreSQL persistence/Redis revocation; 50 passing generated CRUD cases; mutation test detected breakage. |
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

## CH07 verification

- Followed chapter-guide pages 28-30 using the existing app/models, app/schemas,
  Settings, application factory, engine and session architecture.
- User has UUID id, unique email, password_hash, is_verified=False and a
  timezone-aware database-generated created_at. UserRead exposes only public
  fields. A real-database check confirmed defaults, public serialization and
  duplicate-email rejection; temporary user inserts were rolled back.
- Generated the complete Site/User initial migration from a new empty local
  database, careready_ch07. Reviewed and applied revision c8af9d233c2f; a second
  upgrade made no changes and alembic check reported no new operations.
- Removed development startup create_all while preserving resource cleanup.
  With create_all patched to fail if called, readiness returned 200 and site
  create (201), list and read after a second application lifespan succeeded.
  Deleted the verification site (204).
- Compared original practice-site rows before and after: unchanged. Only after
  successful verification, changed the ignored local .env to the new database.
  docs/DEVELOPMENT.md explains the baseline and migration workflow.
- make test: 15 passed. make lint: passed. The pre-existing Starlette/httpx
  deprecation warning remains. No new signup/login routes or Chapter 8 behavior.
- CH06 feature SHA recorded above. CH07 SHA will be recorded in a later update,
  because this commit cannot include its own final SHA.

## CH08 verification

- Followed guide pages 31-33 with UserCreate, the existing UserRead, a user
  service using SQLAlchemy AsyncSession, and an auth router registered inside
  create_app(). POST /api/v1/auth/signup returns 201 with public fields only.
- Email is trimmed and lowercased both at signup and in user lookup, ready for
  reuse by later login work. EmailStr rejects malformed addresses; passwords
  require 6-1024 characters and use SecretStr in the input schema.
- Used the already installed pwdlib 0.3.1 / Argon2 stack; moved pwdlib to runtime
  dependencies. Added email-validator 2.3.0 and dnspython 2.8.0 to the lock. No
  later-chapter tools were installed. Hash work runs outside the async event loop.
- Duplicate normalized emails return 409. The database's unique constraint also
  catches racing signups; the service rolls back before translating the conflict.
- Live checks ran against a disposable local PostgreSQL database upgraded using
  existing migrations. Verified 201, safe response fields, persisted Argon2 hash,
  correct/wrong password verification, repeated mixed-case/space-padded email
  409 after an application restart, and malformed email/password input 422.
- Forced two service requests past the initial lookup concurrently: exactly one
  account persisted, the other raised the duplicate error, and its rolled-back
  session successfully executed another query. Client-supplied is_verified and
  password_hash could not override server values.
- Removed the disposable database; existing development records were unchanged.
  make test: 15 passed; make lint and pip check passed. The existing
  Starlette/httpx deprecation warning remains. No login, tokens or email
  verification behavior was added.
- CH07 feature SHA recorded above; CH08 SHA belongs in a later documentation update.

## CH09 verification

- Added HS256 PyJWT access/refresh tokens with required sub/exp/jti/token_type
  claims; the secret was generated only in ignored .env. .env.example contains
  a placeholder. Promoted existing PyJWT to runtime dependencies; requirements.lock
  already pins the installed PyJWT 2.15.0 and Redis 6.4.0, so no lock change needed.
- Login uses normalized email and existing password verification in a threadpool;
  wrong password/unknown account return identical generic 401 responses. Public
  responses contain no password/hash. Protected site routes reject missing,
  expired, tampered and malformed tokens and accept valid access credentials.
- POST refresh only accepts refresh tokens, checks account existence and issues
  new access tokens. Cross-use of access/refresh and expired refresh are rejected.
- POST logout accepts either token type and revokes just that presented jti using
  the existing Redis client. Observed access-token TTL: 900 seconds; refresh-token
  revocation also has finite TTL. Revocation survived a stopped/restarted API
  process, while separate fresh login tokens remained usable.
- Live checks used fictional accounts and site records in the configured migrated
  development database. All protected CRUD methods worked. Refresh after deleting
  the verification account returned 401. Removed only verification records and
  their exact Redis blocklist keys.
- `make test`: 32 passed. Full lint/format, compile/import and pip check passed.
  Unit tests also verify Redis lookup/write outages return 503 without leaking
  internal details; no successful logout is reported on Redis write failure.
- Existing CH06 CRUD unit tests override authentication only to retain their
  database-contract focus; separate authentication tests exercise real bearer
  validation on every site method. Live checks use the real dependencies.
- No role enforcement, organizations or refresh-token rotation added. See learning
  notes for per-token logout and Redis outage behavior. Feature SHA will be added
  in a later documentation update.

## CH10 verification

- Added default coordinator/admin roles, active account checks, safe `/auth/me`, and explicit role dependencies. Coordinators read sites; admins write. Signup cannot promote itself. See ROLE_MATRIX.md for the permission matrix and local promotion command.
- Applied the additive migration to the configured development database; repeated upgrade and Alembic schema comparison pass. Existing accounts receive the safe coordinator default.
- `make test`: 37 passed; `make lint` passes. Live fictional-account tests verify safe signup, coordinator write rejection for POST/PATCH/DELETE, role promotion taking effect with an existing token, inactive/deleted rejection, admin CRUD, and CH09 refresh/revocation behavior including restart. Verification records and exact Redis keys were cleaned up.
- CH09 feature commit: `baf2c72fb519b34d3945f9866c1f54069a4a2768`. CH10 SHA will be recorded in a later update.

## CH11 verification

See CHAPTER11.md for schema, routes, historical-row handling and live verification. CH10 feature commit: `7b5e0b341c405b14c30888926f0904eebae44508`; its GitHub API checks passed. CH11 feature SHA belongs in the next documentation update.

## CH12 verification

- `SiteNotFound` is raised by site lookup and registered once in the application factory. Read/update/delete and missing-site note/tag paths produce the same 404 message/code without internal details. Existing authentication, validation 422 and successful response contracts remain intact.
- 46 tests and full lint pass. Regression tests check GET/PATCH/DELETE error bodies and malformed IDs; live relationship checks confirm missing-resource envelopes, successful writes and restart persistence. CH11 feature commit: `2da7fa1552cf28076ddfc2c81ab393e62a8f8903`; GitHub checks passed.

## CH13 verification

See CHAPTER13.md for configuration and verified policy behavior. Method, route template, status and timing are logged without credential-bearing request data. Success/error responses and authentication remain intact. CH12 feature commit: `7403cef2001fa0f4c4cb16f285c21ecad7ab13a3`. CH14–CH18 remain pending; no email delivery, background worker or deployment completion is claimed.

## CH14 verification

See CHAPTER14.md for local mail setup, observed results and the remaining one-use/session-invalidation limitations. CH13 feature commit: `644601a64c299c873bc1ffdb45a6697c005a4907`. CH14 SHA will be recorded in a subsequent update.

## CH15 verification

See CHAPTER15.md for worker/Flower commands, live results and delivery limitations. CH14 feature commit: `58ab534`.

## CH16 verification

OpenAPI metadata, tags, fictional site examples and documented auth/not-found responses describe implemented endpoints. Product README separates current single-organization operations from planned tenant/readiness features. Practice routes were removed. Live /docs and /openapi.json checks pass. CH15 feature commit: `6ce49c6`.

## CH17 verification

See TESTING.md for exact disposable setup, commands, scope and results. Real tests use separate ephemeral containers, never development records. CI now runs those checks. CH16 feature commit: `2be48d5`.

## CH18 local preparation (public deployment pending)

Non-root API/worker images, one-shot migrations, persistent isolated PostgreSQL/Redis and sandbox mail containers built and passed the end-to-end demo checks. Lint and 58 tests pass. See DEPLOYMENT.md for commands and rollout/rollback. No public HTTPS URL exists; CH18 remains unchecked until a hosting destination and external checks are complete. CH17 commit: `5ed03b5` (GitHub CI passed).
