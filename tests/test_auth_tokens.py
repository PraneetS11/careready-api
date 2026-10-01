import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import create_token, decode_token, hash_password
from app.db.session import get_session
from app.db.token_store import PREFIX
from app.main import create_app
from app.models.users import User

SECRET = "careready-tests-only-signing-secret-123456"
PASSWORD = "test-account-password"


@pytest.fixture
def auth():
    settings = Settings(_env_file=None, environment="test", jwt_secret_key=SECRET)
    app = create_app(settings)
    session = AsyncMock(spec=AsyncSession)
    user = User(
        is_verified=True,
        id=uuid4(),
        email="demo@example.com",
        password_hash=hash_password(PASSWORD),
        created_at=datetime.now(timezone.utc),
    )
    result = MagicMock()
    result.scalars.return_value.first.return_value = user
    result.scalars.return_value.all.return_value = []
    session.execute.return_value = result
    session.get.return_value = user

    async def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        redis = AsyncMock()
        blocked = set()
        redis.exists.side_effect = lambda key: key in blocked

        async def store(key, value, ex):
            blocked.add(key)

        redis.set.side_effect = store
        app.state.redis = redis
        yield client, settings, session, user, redis


def bearer(token):
    return {"Authorization": "Bearer " + token}


def test_login_normalization_and_generic_errors(auth):
    client, settings, session, user, redis = auth
    good = client.post(
        "/api/v1/auth/login", json={"email": " DEMO@EXAMPLE.COM ", "password": PASSWORD}
    )
    assert good.status_code == 200
    assert set(good.json()) == {"access_token", "refresh_token", "token_type"}
    assert decode_token(good.json()["access_token"], settings)["sub"] == str(user.id)
    assert decode_token(good.json()["refresh_token"], settings)["token_type"] == "refresh"
    assert "demo@example.com" in session.execute.call_args.args[0].compile().params.values()
    wrong = client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": "wrong-password"}
    )
    session.execute.return_value.scalars.return_value.first.return_value = None
    unknown = client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": PASSWORD}
    )
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"detail": "Invalid email or password"}
    assert PASSWORD not in good.text and user.password_hash not in good.text


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("GET", "/api/v1/sites", None),
        ("GET", "/api/v1/sites/" + str(uuid4()), None),
        (
            "POST",
            "/api/v1/sites",
            {"name": "Demo", "city": "Hamilton", "timezone": "America/Toronto"},
        ),
        ("PATCH", "/api/v1/sites/" + str(uuid4()), {"active": False}),
        ("DELETE", "/api/v1/sites/" + str(uuid4()), None),
    ],
)
def test_every_site_operation_requires_auth(auth, method, path, body):
    client, _, session, _, _ = auth
    response = client.request(method, path, **({"json": body} if body else {}))
    assert response.status_code == 401
    session.execute.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.parametrize(
    "kind",
    ["expired", "signature", "missing", "bad_subject", "bad_jti", "bad_type", "wrong_algorithm"],
)
def test_reject_invalid_tokens(auth, kind):
    client, settings, _, user, _ = auth
    payload = decode_token(create_token(user.id, settings), settings)
    key, algorithm = SECRET, "HS256"
    if kind == "expired":
        payload["exp"] = int(time.time()) - 10
    elif kind == "signature":
        key = "different-test-signing-key-long-enough"
    elif kind == "missing":
        del payload["exp"]
    elif kind == "bad_subject":
        payload["sub"] = "invalid"
    elif kind == "bad_jti":
        payload["jti"] = None
    elif kind == "bad_type":
        payload["token_type"] = "other"
    elif kind == "wrong_algorithm":
        algorithm = "HS512"
    token = jwt.encode(payload, key, algorithm=algorithm)
    assert client.get("/api/v1/sites", headers=bearer(token)).status_code == 401
    assert decode_token(token, settings) is None


def test_refresh_role_expiry_and_deleted_user(auth):
    client, settings, session, user, redis = auth
    access, refresh = create_token(user.id, settings), create_token(user.id, settings, "refresh")
    assert client.get("/api/v1/sites", headers=bearer(access)).status_code == 200
    assert client.get("/api/v1/sites", headers=bearer(refresh)).status_code == 401
    assert client.post("/api/v1/auth/refresh", headers=bearer(access)).status_code == 401
    renewed = client.post("/api/v1/auth/refresh", headers=bearer(refresh))
    assert renewed.status_code == 200
    assert renewed.json()["access_token"] != access
    assert (
        client.get("/api/v1/sites", headers=bearer(renewed.json()["access_token"])).status_code
        == 200
    )
    payload = decode_token(refresh, settings)
    payload["exp"] = int(time.time()) - 1
    expired = jwt.encode(payload, SECRET, algorithm="HS256")
    assert client.post("/api/v1/auth/refresh", headers=bearer(expired)).status_code == 401
    session.get.return_value = None
    assert client.post("/api/v1/auth/refresh", headers=bearer(refresh)).status_code == 401


@pytest.mark.parametrize("token_type", ["access", "refresh"])
def test_logout_revokes_only_presented_token_with_ttl(auth, token_type):
    client, settings, _, user, redis = auth
    token = create_token(user.id, settings, token_type)
    data = decode_token(token, settings)
    assert client.post("/api/v1/auth/logout", headers=bearer(token)).status_code == 200
    args = redis.set.call_args
    assert args.args[0] == PREFIX + data["jti"]
    assert 0 < args.kwargs["ex"] <= data["exp"] - int(time.time())
    assert client.post("/api/v1/auth/logout", headers=bearer(token)).status_code == 401
    path = "/api/v1/sites" if token_type == "access" else "/api/v1/auth/refresh"
    method = "GET" if token_type == "access" else "POST"
    assert client.request(method, path, headers=bearer(token)).status_code == 401
    fresh = client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": PASSWORD}
    ).json()
    assert client.get("/api/v1/sites", headers=bearer(fresh["access_token"])).status_code == 200


def test_redis_outage_fails_closed(auth):
    client, settings, _, user, redis = auth
    headers = bearer(create_token(user.id, settings))
    redis.exists.side_effect = ConnectionError("private details")
    response = client.get("/api/v1/sites", headers=headers)
    assert response.status_code == 503 and "private details" not in response.text
    redis.exists.side_effect = None
    redis.exists.return_value = False
    redis.set.side_effect = ConnectionError("private details")
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 503
