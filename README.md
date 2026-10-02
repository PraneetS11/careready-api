# CareReady API

A working single-organization API for fictional care-site operations. This is a development prototype, not a complete equipment-readiness product or a production deployment.

## Implemented

- PostgreSQL site CRUD with UUIDs, active filtering, creators and safe creator summaries.
- Site-specific operational notes and shared tags with duplicate-safe attachment.
- Hashed passwords, JWT login/refresh, Redis token revocation, active-account checks and coordinator/admin permissions.
- Signed, expiring verification and recovery links; verified accounts required for business operations.
- Celery mail delivery to a loopback-only sandbox and local Flower monitoring.
- Health/readiness checks, structured domain errors, secret-conscious request logging, CORS and trusted hosts.
- Automated tests, linting, migrations and GitHub Actions.

## Local setup

Requires Python 3.12 and Docker. Install `requirements.lock` into `.venv`, then install this package with `pip install --no-deps -e .`. Copy `.env.example` to an ignored `.env`; generate a unique random JWT secret of at least 32 characters. Never use the example placeholder as a real secret.

```sh
make services
.venv/bin/alembic upgrade head
docker compose -p careready-mail -f compose.mail.yaml up -d
.venv/bin/celery -A app.tasks:celery_app worker --pool=solo --concurrency=1 --loglevel=INFO
# In another terminal:
make run
```

Open http://127.0.0.1:8002/docs for Swagger, `/redoc` for reference docs, or `/openapi.json` for the contract. The local mailbox is http://127.0.0.1:8027. Sign up, read the sandbox verification link, log in, and paste the access token into Swagger's Authorize control. Signup defaults to coordinator. Deliberate local promotion of an existing account uses `.venv/bin/python -m scripts.promote_admin EMAIL`.

Site writes and tag changes require admin; verified coordinators can read sites and add/read operational notes. The signup response confirms account creation, not mail delivery. A separate worker must run to deliver mail. Practice endpoints have been removed from the product app.

Run `make test` and `make lint`. Stop the worker with Ctrl-C and Compose services with `docker compose stop`; this preserves database volumes. See [development instructions](docs/DEVELOPMENT.md) and [role permissions](docs/ROLE_MATRIX.md).

## Planned and limitations

Organizations, tenant isolation, equipment stock/reservations, readiness workflows, purchase approvals, shipments/returns, audit retention and reporting are not implemented. Refresh-token rotation, single-use recovery links, reset-session invalidation, reliable outbox delivery and a public HTTPS deployment remain future work. Do not store patient, employee or customer information. Use fictional examples only. No license has been selected.

Local containers, verified checks and pending public deployment: [Deployment](docs/DEPLOYMENT.md).
