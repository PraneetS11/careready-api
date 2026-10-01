# Development workflow

Use a separate virtual environment and Git repository for each product. The current dependency lock includes development and future-progression libraries; installed libraries are not implemented features.

## Daily work

```bash
git switch -c feat/describe-one-change
make services
make test
make lint
git diff
git add <specific-files>
git commit -m "feat: describe the working behavior"
git push -u origin HEAD
```

Review the diff for secrets and unrelated files before committing. Make one focused change, its tests, and relevant documentation per commit. Do not backdate commits or claim planned features as delivered. Initial history reflects actual scaffold, API, tests, infrastructure, and documentation work.

## Local service isolation

CareReady: API 8002, PostgreSQL 5434, Redis 6382. Compose uses its own named volume and network. Local credentials are deliberately non-production. Copy `.env.example` without overwriting an existing `.env`.

## Dependency updates

```bash
.venv/bin/python -m pip install --upgrade -e '.[dev,progression]'
.venv/bin/python -m pip freeze --exclude-editable > requirements.lock
make test
make lint
```

The lock is a pinned Python environment snapshot, not a cryptographically verified supply-chain lock. Validate on CI Linux as well as the local Mac. For production, derive a runtime-only lock and scan dependencies/images.

## Container smoke test

```bash
docker build -t careready-api:dev .
docker run --rm -p 127.0.0.1:8002:8000 --env-file .env careready-api:dev
```

Inside a container, 127.0.0.1 means the container itself. For readiness with Mac-hosted Compose ports, set DATABASE_URL and REDIS_URL to host.docker.internal instead of 127.0.0.1, or attach an API service to the Compose network and use postgres:5432 and redis:6379. The Dockerfile is a starting recipe; the supplied Compose file runs dependencies only.

## Planned hosted release

Deploy API and workers separately; run Alembic as a controlled release step once migrations exist. Configure managed PostgreSQL, private Redis, secret storage, TLS, allowed hosts/origins, rate limiting, structured logs, metrics, backups, and restore drills. Use /health/live for restarts and /health/ready for traffic gating. No hosted deployment is provisioned by this starter.

## Timestamp-aligned development

Use BUILD_PROGRESSION.md for watch ranges and exact commit checkpoints, and PROGRESS.md to record real dates, SHAs, and evidence. Video time is a pause marker; commit only after the relevant behavior and tests pass. Existing setup commits are already complete and must not be recreated.

## Chapter 7: migration-managed development database

The original `careready` database remains separate with its practice rows intact.
On 2026-09-30, created the empty local database `careready_ch07`, generated and
reviewed revision `c8af9d233c2f`, and applied it before changing the ignored local
`.env` DATABASE_URL to target that database. No credentials are stored in Alembic
configuration. The complete initial revision creates `site` and `user`, with
UUID primary keys, a unique user email and a timezone-aware creation timestamp.

For this existing local setup, start services and migrate before starting the API:

```bash
make services
.venv/bin/python -m alembic upgrade head
make run
```

For a fresh local setup, create an empty database using the configured local
PostgreSQL role, set the ignored `.env` DATABASE_URL to it, then run the same
migration command. Do not apply this initial migration over the old practice
schema or blindly stamp it as migrated. Preserve that database until any desired
data transfer has been planned separately. Configuration continues to come from
Settings; an environment DATABASE_URL overrides `.env`.

Application startup no longer runs `create_all`; it still owns engine and Redis
cleanup. The unused Chapter 5 helper remains for historical reference, not as a
startup step. For future model changes, import each table in `migrations/env.py`,
generate a revision, review it, then upgrade. Check schema agreement with:

```bash
.venv/bin/python -m alembic current
.venv/bin/python -m alembic check
```

`UserRead` contains only id, email, is_verified and created_at. The stored
password_hash is excluded: a storage model must not be used as a public response
or future password input schema. This chapter adds no account creation or login
routes.

Verification: empty-database upgrade and repeat upgrade passed; Alembic reported
no new operations. Real PostgreSQL rejected duplicate emails. Site create/list
and read after a fresh app lifespan passed without startup DDL; the verification
site was deleted. The original database's site rows were unchanged. Existing
15 tests and full lint pass; the existing Starlette/httpx deprecation warning
remains.

## Chapter 9 authentication configuration

Set JWT_SECRET_KEY to a random secret of at least 32 characters in ignored .env
before starting the API. Generate one with `python -c "import secrets;
print(secrets.token_urlsafe(48))"` and save it locally; never commit its value.
JWT_ALGORITHM is HS256. ACCESS_TOKEN_MINUTES defaults to 15 and
REFRESH_TOKEN_DAYS to 2. JWT settings are read by the existing Settings class.
A missing secret prevents normal development/production startup.

Use POST /api/v1/auth/login with email/password JSON. Send the returned access
JWT as `Authorization: Bearer <token>` for /api/v1/sites. Send the refresh JWT
to POST /api/v1/auth/refresh; POST /api/v1/auth/logout revokes whichever token
you present. Keep the existing Redis service running for validation and logout.
