import re
import subprocess
import time
from pathlib import Path
from uuid import uuid4

import httpx

book = False
project = "careready"
root = Path(__file__).resolve().parents[1]
compose = [
    "docker",
    "compose",
    "--env-file",
    ".env.demo",
    "-p",
    project + "-demo",
    "-f",
    "compose.demo.yaml",
]


def dc(*args):
    return subprocess.run(
        compose + list(args), cwd=root, check=True, capture_output=True, text=True
    ).stdout


client = httpx.Client(base_url="http://127.0.0.1:" + ("8008" if book else "8009"), timeout=20)
mail = httpx.Client(base_url="http://127.0.0.1:" + ("8028" if book else "8029"), timeout=5)


def check(r, status):
    assert r.status_code == status, (
        r.request.method,
        re.sub(r"/verify/.*", "/verify/<redacted>", r.request.url.path),
        r.status_code,
        status,
    )
    return r


endpoint = "/api/v1/books/" if book else "/api/v1/sites"
auth = "/api/v1/auth"
email = "container-" + uuid4().hex[:12] + "@example.com"
password = "Fictional-" + uuid4().hex
uid = ident = None
mail_ids = []


def wait_ready():
    for _ in range(100):
        try:
            if client.get("/health/ready").status_code == 200:
                return
        except httpx.TransportError:
            pass
        time.sleep(0.2)
    raise AssertionError("Readiness did not recover")


try:
    wait_ready()
    check(client.get("/health/live"), 200)
    check(client.get("/health/live", headers={"Host": "untrusted.invalid"}), 400)
    check(client.get(endpoint), 403 if book else 401)
    credentials = {"email": email, "password": password}
    payload = dict(credentials)
    if book:
        payload.update(username="demo", first_name="Fictional", last_name="Demo")
    uid = check(client.post(auth + "/signup", json=payload), 201).json()["uid" if book else "id"]
    access = check(client.post(auth + "/login", json=credentials), 200).json()["access_token"]
    headers = {"Authorization": "Bearer " + access}
    check(client.get(endpoint, headers=headers), 403)
    for _ in range(100):
        matches = [
            m
            for m in mail.get("/api/v1/messages").json()["messages"]
            if any(t["Address"] == email for t in m["To"])
        ]
        if matches:
            break
        time.sleep(0.2)
    assert len(matches) == 1, "Worker did not deliver exactly one signup message"
    mail_ids = [m["ID"] for m in matches]
    body = mail.get("/api/v1/message/" + mail_ids[0]).json()["Text"]
    token = body.strip().split("/")[-1]
    check(client.get(auth + "/verify/" + token), 200)
    check(client.get(endpoint, headers=headers), 200)
    body = (
        {
            "title": "Fictional container book",
            "author": "Demo",
            "publisher": "Demo",
            "published_date": "2024-01-01",
            "page_count": 12,
            "language": "English",
        }
        if book
        else {"name": "Fictional container site", "city": "Hamilton", "timezone": "America/Toronto"}
    )
    if not book:
        check(client.post(endpoint, json=body, headers=headers), 403)
        dc(
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            "demo",
            "-d",
            "demo",
            "-c",
            f"""UPDATE "user" SET role='admin' WHERE id='{uid}';""",
        )
    ident = check(client.post(endpoint, json=body, headers=headers), 201).json()[
        "uid" if book else "id"
    ]
    detail = endpoint.rstrip("/") + "/" + ident
    dc("restart", "api")
    wait_ready()
    check(client.get(detail, headers=headers), 200)
    check(client.request("GET" if book else "POST", auth + "/logout", headers=headers), 200)
    dc("restart", "api", "redis")
    wait_ready()
    check(client.get(endpoint, headers=headers), 403 if book else 401)
    # A stopped dependency changes readiness, not process liveness.
    dc("stop", "redis")
    check(client.get("/health/ready"), 503)
    check(client.get("/health/live"), 200)
    dc("start", "redis")
    wait_ready()
    logs = dc("logs", "--no-color", "api", "worker")
    assert (
        password not in logs and access not in logs and token not in logs and email not in logs
    ), "Sensitive payload appeared in logs"
    assert dc("exec", "-T", "api", "id", "-u").strip() != "0"
    assert dc("exec", "-T", "worker", "id", "-u").strip() != "0"
    print(
        project
        + " PASS: containers, migrations, worker mail, roles, persistence, revocation and recovery"
    )
finally:
    dc("start", "redis")
    if ident:
        table, column = ("books", "uid") if book else ("site", "id")
        dc(
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            "demo",
            "-d",
            "demo",
            "-c",
            f"DELETE FROM {table} WHERE {column}='{ident}';",
        )
    if uid:
        table, column = ("user_accounts", "uid") if book else ('"user"', "id")
        dc(
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            "demo",
            "-d",
            "demo",
            "-c",
            f"DELETE FROM {table} WHERE {column}='{uid}';",
        )
    if mail_ids:
        mail.request("DELETE", "/api/v1/messages", json={"IDs": mail_ids})
    client.close()
    mail.close()
