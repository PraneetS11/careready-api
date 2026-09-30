# CareReady chapter progress

One assignment after completing each matching Bookly chapter. This chapter edition supersedes C01-C29 and the small P/E-checkpoint draft. Prior tracker: archive/guide-v1/PROGRESS.md. No chapter is marked complete automatically.

Record real date and proof before the chapter commit; add its SHA in the next documentation update.

| Done | Chapter | Video end | Assignment | Actual date | Feature SHA | Success evidence / blocker |
|---|---|---|---|---|---|---|
| [ ] | CH01 | 0:07:30 | Installation and project setup | | | |
| [ ] | CH02 | 0:49:43 | Creating a simple web server | | | |
| [ ] | CH03 | 1:23:37 | Building a CRUD REST API | | | |
| [ ] | CH04 | 1:38:22 | Large project structure using routers | | | |
| [x] | CH05 | 2:29:48 | Databases with SQLModel | 2026-09-30 | | Local PostgreSQL/Redis healthy; readiness 200 on two startups; one site table with UUID primary key and all five required columns; clean shutdown twice; 8 tests pass. See verification below. |
| [ ] | CH06 | 3:33:35 | Finishing the database CRUD | | | |
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
- Ruff lint and format checks pass for all changed Python files and tests.
  Full-project lint still has the pre-existing import-spacing issue in
  `app/api/sites.py`; full-project format checks flag that file and
  `app/api/site_data.py`. These unchanged Chapter 4 files were left intact.
- HTTP site CRUD still uses memory and integer ids until CH06. Table initialization
  runs only in development; tests explicitly use the test environment.
- Feature SHA is left blank in the implementation commit; record it in a later
  documentation update after the commit exists.
