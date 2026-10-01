from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_access_token
from app.core.config import Settings
from app.db.session import get_session
from app.main import create_app
from app.models.users import User
from app.schemas.users import UserCreate


@pytest.fixture
def role_client():
    user = User(
        is_verified=True,
        email="roles@example.com",
        password_hash="hidden",
        created_at=datetime.now(timezone.utc),
    )
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = user
    app = create_app(Settings(_env_file=None, environment="test"))
    app.dependency_overrides[require_access_token] = lambda: {"sub": str(user.id)}

    async def get_db():
        yield session

    app.dependency_overrides[get_session] = get_db
    with TestClient(app) as client:
        yield client, user, session


def test_me_safe_default_role_and_deleted_or_inactive_user(role_client):
    client, user, session = role_client
    result = client.get("/api/v1/auth/me")
    assert result.status_code == 200
    assert result.json()["role"] == "coordinator"
    assert "password_hash" not in result.json()
    user.is_active = False
    assert client.get("/api/v1/auth/me").status_code == 401
    session.get.return_value = None
    assert client.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize(
    "method,path,data",
    [
        ("POST", "/api/v1/sites", {"name": "Demo", "city": "Hamilton", "timezone": "UTC"}),
        ("PATCH", "/api/v1/sites/" + str(uuid4()), {"active": False}),
        ("DELETE", "/api/v1/sites/" + str(uuid4()), None),
    ],
)
def test_coordinator_cannot_write(role_client, method, path, data):
    client, user, session = role_client
    response = client.request(method, path, **({"json": data} if data else {}))
    assert response.status_code == 403
    session.commit.assert_not_awaited()


def test_admin_create_and_signup_cannot_choose_role(role_client):
    client, user, session = role_client
    user.role = "admin"
    result = client.post(
        "/api/v1/sites", json={"name": "Demo", "city": "Hamilton", "timezone": "UTC"}
    )
    assert result.status_code == 201
    assert (
        "role"
        not in UserCreate(
            email="roles@example.com", password="long-password", role="admin"
        ).model_dump()
    )
    assert (
        User(
            is_verified=True,
        ).role
        == "coordinator"
    )
