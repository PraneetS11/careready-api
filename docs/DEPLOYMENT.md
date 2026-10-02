# Chapter 18: container preparation and deployment status

Local container verification is complete. **Public HTTPS deployment is pending: no hosting provider/server or domain has been selected.** No public URL is claimed. The online Bookly documentation currently ends with API Documentation (Chapter 16); this deployment exercise follows the CareReady guide's Chapter 18 concepts for both projects.

## Run the local fictional-data demo

Install Docker and the repository's development dependencies. From the repository root:

```sh
.venv/bin/python scripts/init_demo_env.py
docker compose --env-file .env.demo -p careready-demo -f compose.demo.yaml up -d --build --wait
.venv/bin/python scripts/verify_demo.py
```

The initialization helper creates random credentials only if `.env.demo` does not exist; keep the existing file on later runs. The API is at http://127.0.0.1:8009/docs, readiness at `/health/ready`, liveness at `/health/live`, and sandbox mailbox at http://127.0.0.1:8029. These are local HTTP addresses, not public HTTPS deployments. Signup sends to this mailbox through the separate Celery worker. No real recipient receives mail.

Compose builds one non-root image shared by API, worker and a one-shot Alembic migration service. The API waits for successful migration and healthy Redis. PostgreSQL and Redis have project-specific named volumes and no published host ports. Redis append-only persistence retains revocation and queue state across restart. Mailpit's UI and API bind to loopback. `.dockerignore` excludes credentials, virtual environments and Git history; secrets enter at runtime. Do not print expanded Compose configuration or commit `.env.demo`.

`verify_demo.py` is intentionally restricted to this local demo project. It creates and removes only its fictional account, book/site and mailbox messages. It restarts the demo API and Redis and temporarily stops Redis; do not run it against a shared demo in use. It checks worker delivery, unverified access denial, role rules, persistence, revoked-token rejection, readiness 503 during an outage, recovery, non-root execution and absence of its credentials/email tokens in logs.

Local results: both images built and migrations ran from empty databases; all those smoke checks passed. Bookly's full suite: 35 tests plus 18 subtests. CareReady: 58 tests and lint passed. Chapter 17 GitHub CI passed for both repositories. CI now also builds the Docker image; the Chapter 18 CI result must be checked on its actual commit.

Stop the demo without deleting persistent data:

```sh
docker compose --env-file .env.demo -p careready-demo -f compose.demo.yaml down
```

Do not add `--volumes` unless intentionally erasing this demo. Changing the password environment value does not change the password already stored in an initialized PostgreSQL volume.

## Hosting handoff and release checklist

Choose a provider/server and domain before publishing. Use fictional data for this single-organization course demo. Keep PostgreSQL, Redis, the worker and mailbox private. Terminate HTTPS at the chosen provider/reverse proxy; publish only the API. Set `PUBLIC_BASE_URL` to the real HTTPS URL, `ALLOWED_HOSTS` to a JSON list of exact hostnames, and `CORS_ORIGINS` to exact approved frontend origins. Keep credentials in the provider's runtime secret store. If using managed PostgreSQL, configure its required TLS; the local Compose network's plaintext database connection is not a managed-database configuration. Sandbox mail remains private; remote mailbox access should use an authenticated tunnel.

Build/tag an immutable release image, back up the database, run `alembic upgrade head` exactly once as a release job, then start API and worker. Check the actual release's CI, health, signup/verification, role denial, CRUD across restart, worker completion and sanitized logs. Record the real URL and commit only after external HTTPS checks pass. Database readiness alone does not prove worker/mail delivery.

For rollback, retain the previous image and its matching config. Roll back the API/worker image only if the schema remains compatible. Do not blindly downgrade migrations or erase volumes: a schema reversal can discard data. Restore a tested backup or apply a reviewed forward fix when compatibility is uncertain. Public deployment, TLS, provider secrets/backups and remote rollout/rollback remain unverified until hosting is selected.
