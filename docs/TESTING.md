# Testing

Unit/API tests replace dependencies with AsyncMock for awaited calls and ordinary mocks for synchronous result objects. Integration tests are opt-in and deliberately hard-code the local disposable services; they never target `.env` database URLs. They truncate only the test database and flush only its dedicated Redis container between runs. Never repoint those fixed test ports at another database.

```sh
docker compose -p careready-ch17-test -f compose.test.yaml up -d --wait
RUN_INTEGRATION=1 .venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_isolated.py --contracts
docker compose -p careready-ch17-test -f compose.test.yaml down
```

Install the pinned development dependencies first (requirements.lock). PostgreSQL is ephemeral; no development volumes are mounted. The script migrates an empty database, runs the real API/lifespan, registers a fictional account, verifies role/authentication rules, proves stored data and Redis revocation survive process restart, and resets test state. Mail is queued only to the disposable Redis broker with no running worker, so no SMTP delivery occurs.

Schemathesis 4.28.0 was checked with `run --help`. The script invokes `schemathesis run <disposable-url>/openapi.json --include-path-regex <CRUD-pattern> --phases examples,fuzzing --max-examples 10 --seed 17 --checks not_a_server_error,status_code_conformance,response_schema_conformance --header 'Authorization:Bearer <temporary-access-token>' --output-sanitize true --generation-database :memory:`. The precise project-specific filter is committed in the script. Only the five core site CRUD operations are fuzzed; this is not an exhaustive all-route/security audit. Generated requests can change/delete data, which is why the target must be disposable.

Verified 2026-10-01: 58 tests pass twice, including reverse file order and real PostgreSQL/Redis integration. Schemathesis generated 50 passing cases across five operations with no server errors, undocumented statuses or response-schema violations. A deliberate in-memory mutation of password verification made the new CareReady security test fail, and was restored before the passing suite. CI now starts the same isolated resources and runs integration plus contracts.

Contract testing found and fixed null-character inputs that PostgreSQL cannot store; Bookly also gained PostgreSQL integer bounds and an empty-database bootstrap for its legacy pre-Alembic books table. Malformed-body 400 responses are now documented. No development rows were modified by these tests.
