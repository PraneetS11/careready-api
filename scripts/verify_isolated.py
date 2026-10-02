"""Only targets the fixed disposable services in compose.test.yaml."""

import asyncio
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from uuid import uuid4

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

BOOK = False
ROOT = Path(__file__).resolve().parents[1]
PGPORT = 5446
REDISPORT = 6396
DATABASE = f"postgresql+asyncpg://ch17:disposable-test-only@127.0.0.1:{PGPORT}/ch17"
ENV = dict(
    os.environ,
    DATABASE_URL=DATABASE,
    DATABASE_SSL="false",
    JWT_SECRET_KEY=secrets.token_hex(32),
    ENVIRONMENT="test",
    REDIS_URL=f"redis://127.0.0.1:{REDISPORT}/0",
    CELERY_BROKER_URL=f"redis://127.0.0.1:{REDISPORT}/1",
    CELERY_RESULT_BACKEND=f"redis://127.0.0.1:{REDISPORT}/2",
)
PYTHON = str(ROOT / ".venv/bin/python")


async def promote(uid):
    engine = create_async_engine(DATABASE)
    async with engine.begin() as conn:
        table, column = ("user_accounts", "uid") if BOOK else ('"user"', "id")
        await conn.execute(
            text(f"UPDATE {table} SET is_verified=true, role='admin' WHERE {column}=:id"),
            {"id": uid},
        )
    await engine.dispose()


async def reset_state():
    # Restricted to the hard-coded disposable database; never read .env here.
    engine = create_async_engine(DATABASE)
    async with engine.begin() as conn:
        tables = (
            "booktag,reviews,tags,books,user_accounts"
            if BOOK
            else 'sitetaglink,sitenote,sitetag,site,"user"'
        )
        await conn.execute(text("TRUNCATE " + tables + " CASCADE"))
    await engine.dispose()
    from redis.asyncio import Redis

    for db in (0, 1, 2):
        cache = Redis.from_url(f"redis://127.0.0.1:{REDISPORT}/{db}")
        await cache.flushdb()
        await cache.aclose()


def main():
    subprocess.run(
        [str(ROOT / ".venv/bin/alembic"), "upgrade", "head"], cwd=ROOT, env=ENV, check=True
    )
    asyncio.run(reset_state())
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    log = tempfile.TemporaryFile(mode="w+")
    proc = None
    client = httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=20)

    def stop():
        if proc is not None and proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=20)

    def start():
        nonlocal proc
        proc = subprocess.Popen(
            [
                PYTHON,
                "-m",
                "uvicorn",
                "src:app" if BOOK else "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--no-access-log",
            ],
            cwd=ROOT,
            env=ENV,
            stdout=log,
            stderr=log,
        )
        for _ in range(100):
            if proc.poll() is not None:
                raise RuntimeError("Disposable API failed to start")
            try:
                if client.get("/openapi.json").status_code == 200:
                    return
            except httpx.TransportError:
                pass
            time.sleep(0.1)
        raise RuntimeError("API startup timed out")

    def expect(response, status):
        assert response.status_code == status, (
            response.request.method,
            response.request.url.path,
            response.status_code,
            status,
        )
        return response

    try:
        start()
        auth = "/api/v1/auth"
        endpoint = "/api/v1/books/" if BOOK else "/api/v1/sites"
        credentials = {
            "email": "integration@example.com",
            "password": "Fictional-integration-password",
        }
        signup = dict(credentials)
        if BOOK:
            signup.update(first_name="Demo", last_name="Test", username="test")
        uid = expect(client.post(auth + "/signup", json=signup), 201).json()[
            "uid" if BOOK else "id"
        ]
        access = expect(client.post(auth + "/login", json=credentials), 200).json()["access_token"]
        headers = {"Authorization": "Bearer " + access}
        expect(client.get(endpoint), 403 if BOOK else 401)
        expect(client.get(endpoint, headers=headers), 403)
        if not BOOK:

            async def verify_only():
                engine = create_async_engine(DATABASE)
                async with engine.begin() as conn:
                    await conn.execute(
                        text('UPDATE "user" SET is_verified=true WHERE id=:id'), {"id": uid}
                    )
                await engine.dispose()

            asyncio.run(verify_only())
            expect(
                client.post(
                    endpoint,
                    headers=headers,
                    json={
                        "name": "No permission",
                        "city": "Hamilton",
                        "timezone": "America/Toronto",
                    },
                ),
                403,
            )
        asyncio.run(promote(uid))
        body = (
            {
                "title": "Fictional persisted book",
                "author": "Test",
                "publisher": "Test",
                "published_date": "2024-01-01",
                "page_count": 10,
                "language": "English",
            }
            if BOOK
            else {
                "name": "Fictional persisted site",
                "city": "Hamilton",
                "timezone": "America/Toronto",
            }
        )
        item = expect(client.post(endpoint, json=body, headers=headers), 201).json()
        ident = item["uid" if BOOK else "id"]
        detail = endpoint.rstrip("/") + "/" + ident
        expect(client.post(endpoint, json={}, headers=headers), 422)
        expect(client.get(endpoint.rstrip("/") + "/" + str(uuid4()), headers=headers), 404)
        stop()
        start()
        assert (
            expect(client.get(detail, headers=headers), 200).json()["uid" if BOOK else "id"]
            == ident
        )
        if not BOOK:
            expect(client.patch(detail, json={"active": False}, headers=headers), 200)
            active = expect(client.get(endpoint + "?active=true", headers=headers), 200).json()
            assert ident not in {r["id"] for r in active}
        expect(client.request("GET" if BOOK else "POST", auth + "/logout", headers=headers), 200)
        stop()
        start()
        expect(client.get(endpoint, headers=headers), 403 if BOOK else 401)
        access = expect(client.post(auth + "/login", json=credentials), 200).json()["access_token"]
        if "--contracts" in sys.argv:
            path = r"^/api/v1/books" if BOOK else r"^/api/v1/sites(?:/\{site_id\})?$"
            cmd = [
                str(ROOT / ".venv/bin/schemathesis"),
                "run",
                f"http://127.0.0.1:{port}/openapi.json",
                "--include-path-regex",
                path,
                "--phases",
                "examples,fuzzing",
                "--max-examples",
                "10",
                "--seed",
                "17",
                "--checks",
                "not_a_server_error,status_code_conformance,response_schema_conformance",
                "--header",
                "Authorization:Bearer " + access,
                "--output-sanitize",
                "true",
                "--generation-database",
                ":memory:",
            ]
            result = subprocess.run(
                cmd, cwd=ROOT, env=ENV, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )
            print(result.stdout)
            assert result.returncode == 0, "Contract checks failed"
        fresh_headers = {"Authorization": "Bearer " + access}
        fresh = expect(client.post(endpoint, json=body, headers=fresh_headers), 201).json()
        detail = endpoint.rstrip("/") + "/" + fresh["uid" if BOOK else "id"]
        expect(client.delete(detail, headers={"Authorization": "Bearer " + access}), 204)
        expect(client.get(detail, headers={"Authorization": "Bearer " + access}), 404)
        print(
            "PASS: isolated PostgreSQL persistence, validation/filtering, "
            "authorization and Redis revocation survive restarts"
        )
    finally:
        stop()
        client.close()
        log.close()
        asyncio.run(reset_state())


if __name__ == "__main__":
    main()
