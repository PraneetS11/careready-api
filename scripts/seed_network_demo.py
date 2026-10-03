"""Seed explicit fictional accounts in the local Docker demo, never a remote target."""

import time
from datetime import datetime, timedelta, timezone

import httpx

PASSWORD = "CareReady-demo-2026!"
client = httpx.Client(base_url="http://127.0.0.1:8080", timeout=20)
mail = httpx.Client(base_url="http://127.0.0.1:8029", timeout=10)


def check(response, expected=200):
    if response.status_code != expected:
        raise RuntimeError(f"Demo setup failed: HTTP {response.status_code}")
    return response.json()


def account(role, name, **extras):
    email = role + "@demo.careready.example"
    data = dict(role=role, name=name, email=email, password=PASSWORD, **extras)
    created = client.post("/api/v1/network/register", json=data)
    if created.status_code not in (201, 409):
        check(created, 201)
    if created.status_code == 201:
        for _ in range(100):
            messages = check(mail.get("/api/v1/messages"))["messages"]
            matches = [m for m in messages if any(t["Address"] == email for t in m["To"])]
            if matches:
                body = check(mail.get("/api/v1/message/" + matches[0]["ID"]))["Text"]
                token = body.strip().split("/")[-1]
                check(client.get("/api/v1/auth/verify/" + token))
                break
            time.sleep(0.2)
        else:
            raise RuntimeError("Demo verification mail did not arrive")
    pair = check(client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD}))
    headers = {"Authorization": "Bearer " + pair["access_token"]}
    return check(client.get("/api/v1/network/me", headers=headers)), headers


def run():
    agency, ah = account("agency", "Alex Morgan", agency_name="Evergreen Home Care", city="Toronto")
    aid = agency["profile"]["agency_id"]
    requester, rh = account("requester", "Jamie Parker")
    provider, ph = account(
        "provider",
        "Sam Rivera",
        agency_id=aid,
        experience=3,
        gender="nonbinary",
        services=["companionship", "personal_care", "nursing", "respite"],
        languages=["English", "French"],
    )
    check(
        client.patch("/api/v1/network/team/" + provider["id"], headers=ah, json={"approved": True})
    )
    existing = check(client.get("/api/v1/network/visits", headers=rh))
    if not existing:
        start = (datetime.now(timezone.utc) + timedelta(days=2)).replace(
            hour=15, minute=0, second=0, microsecond=0
        )
        for i, service in enumerate(["companionship", "personal_care", "nursing", "respite"]):
            visits = check(
                client.post(
                    "/api/v1/network/visits",
                    headers=rh,
                    json=dict(
                        agency_id=aid,
                        service=service,
                        recipient="Fictional recipient " + str(i + 1),
                        address="Fictional demo address " + str(i + 1),
                        city="Toronto",
                        starts_at=(start + timedelta(days=i)).isoformat(),
                        duration_minutes=60 + i * 30,
                        occurrences=2 if i == 0 else 1,
                        min_experience=min(i, 2),
                        preferred_language="French" if i == 0 else "any",
                        communication="slow_clear" if i == 0 else "standard",
                        pets_present=i == 1,
                        notes="Fictional demonstration record. No real recipient information.",
                        consent_confirmed=True,
                    ),
                ),
                201,
            )
            for v in visits:
                if i != 3:
                    check(
                        client.post(
                            "/api/v1/network/visits/" + v["id"] + "/transition",
                            headers=ah,
                            json={"action": "publish"},
                        )
                    )
                if i == 2:
                    check(
                        client.post(
                            "/api/v1/network/jobs/" + v["id"] + "/accept", headers=ph, json={}
                        )
                    )
    if not check(client.get("/api/v1/network/devices", headers=ah)):
        for name, code, status in [
            ("Portable blood pressure monitor", "EV-001", "available"),
            ("Mobility support walker", "EV-002", "in_use"),
            ("Pulse oximeter", "EV-003", "maintenance"),
        ]:
            check(
                client.post(
                    "/api/v1/network/devices",
                    headers=ah,
                    json=dict(name=name, asset_code=code, status=status),
                ),
                201,
            )
    print("Fictional demo ready. Account details are in docs/CARE_NETWORK.md.")


if __name__ == "__main__":
    try:
        run()
    finally:
        client.close()
        mail.close()
