"""Exercise network isolation and concurrent acceptance against disposable services only."""

import asyncio
import socket
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import httpx
import verify_isolated as base
from itsdangerous import URLSafeTimedSerializer


def run():
    subprocess.run(
        [str(base.ROOT / ".venv/bin/alembic"), "upgrade", "head"],
        cwd=base.ROOT,
        env=base.ENV,
        check=True,
    )
    asyncio.run(base.reset_state())
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    with tempfile.TemporaryFile(mode="w+") as log:
        proc = subprocess.Popen(
            [base.PYTHON, "-m", "uvicorn", "app.main:app", "--port", str(port), "--no-access-log"],
            cwd=base.ROOT,
            env=base.ENV,
            stdout=log,
            stderr=log,
        )
        client = httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=20)

        def check(response, status):
            assert response.status_code == status, (
                response.request.method,
                response.request.url.path.split("/verify/")[0],
                response.status_code,
                status,
            )
            return response.json()

        def register(role, label, **kwargs):
            body = dict(
                role=role,
                name=label,
                email=label + "@example.com",
                password="Fictional-long-password",
                **kwargs,
            )
            account = check(client.post("/api/v1/network/register", json=body), 201)
            token = URLSafeTimedSerializer(
                base.ENV["JWT_SECRET_KEY"], salt="careready-email-verify"
            ).dumps({"user_id": account["id"]})
            check(client.get("/api/v1/auth/verify/" + token), 200)
            access = check(client.post("/api/v1/auth/login", json=body), 200)["access_token"]
            return account, {"Authorization": "Bearer " + access}

        try:
            for _ in range(100):
                try:
                    if client.get("/health/live").status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                time.sleep(0.1)
            agency, ah = register("agency", "agency", agency_name="Fictional agency")
            other, oh = register("agency", "other", agency_name="Other agency")
            agency_id = check(client.get("/api/v1/network/me", headers=ah), 200)["profile"][
                "agency_id"
            ]
            req, rh = register("requester", "requester")
            stranger, sh = register("requester", "stranger")
            p1, h1 = register(
                "provider",
                "provider-one",
                agency_id=agency_id,
                experience=2,
                services=["companionship"],
                languages=["French"],
            )
            p2, h2 = register(
                "provider",
                "provider-two",
                agency_id=agency_id,
                experience=2,
                services=["companionship"],
            )
            url = "/api/v1/network"
            check(client.patch(url + "/team/" + p1["id"], headers=oh, json={"approved": True}), 404)
            data = dict(
                agency_id=agency_id,
                service="companionship",
                recipient="Private recipient",
                address="Private address",
                city="Toronto",
                starts_at=(datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
                occurrences=2,
                min_experience=2,
                preferred_language="French",
                consent_confirmed=True,
            )
            visits = check(client.post(url + "/visits", headers=rh, json=data), 201)
            assert len(visits) == 2 and visits[0]["series_id"] == visits[1]["series_id"]
            assert check(client.get(url + "/visits", headers=sh), 200) == []
            check(
                client.post(
                    url + "/visits/" + visits[0]["id"] + "/transition",
                    headers=oh,
                    json={"action": "publish"},
                ),
                404,
            )
            for v in visits:
                check(
                    client.post(
                        url + "/visits/" + v["id"] + "/transition",
                        headers=ah,
                        json={"action": "publish"},
                    ),
                    200,
                )
            assert check(client.get(url + "/jobs", headers=h1), 200) == []
            for provider in (p1, p2):
                check(
                    client.patch(
                        url + "/team/" + provider["id"], headers=ah, json={"approved": True}
                    ),
                    200,
                )
            jobs = check(client.get(url + "/jobs", headers=h1), 200)
            assert len(jobs) == 2 and jobs[0]["language_match"]
            assert not {"address", "recipient", "notes", "requester_id"} & jobs[0].keys()
            accept = url + "/jobs/" + visits[0]["id"] + "/accept"
            with ThreadPoolExecutor(2) as pool:
                responses = list(pool.map(lambda h: client.post(accept, headers=h), [h1, h2]))
            assert sorted(r.status_code for r in responses) == [200, 409]
            winner = h1 if responses[0].status_code == 200 else h2
            assert (
                check(client.get(url + "/visits", headers=winner), 200)[0]["address"]
                == "Private address"
            )
            # Same-time second request must not appear or be accepted by this worker.
            duplicate = check(
                client.post(url + "/visits", headers=rh, json=dict(data, occurrences=1)), 201
            )[0]
            check(
                client.post(
                    url + "/visits/" + duplicate["id"] + "/transition",
                    headers=ah,
                    json={"action": "publish"},
                ),
                200,
            )
            check(client.post(url + "/jobs/" + duplicate["id"] + "/accept", headers=winner), 409)
            check(
                client.post(
                    url + "/visits/" + visits[0]["id"] + "/transition",
                    headers=rh,
                    json={"action": "complete"},
                ),
                409,
            )
            device = check(
                client.post(
                    url + "/devices",
                    headers=ah,
                    json={"name": "Fictional monitor", "asset_code": "DEMO-1"},
                ),
                201,
            )
            check(
                client.patch(
                    url + "/devices/" + device["id"], headers=oh, json={"status": "maintenance"}
                ),
                404,
            )
            assert check(client.get(url + "/devices", headers=oh), 200) == []
            print("PASS: network isolation, recurrence, preferences and acceptance races")
        finally:
            proc.terminate()
            proc.wait(timeout=20)
            client.close()
            asyncio.run(base.reset_state())


if __name__ == "__main__":
    run()
