from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.config import Settings
from app.db.session import get_session
from app.main import create_app
from app.models.sites import Site
from app.models.users import User
from app.schemas.sites import SiteCreate, SiteUpdate
from app.services.sites import SiteService

VALUES = {"name": "Test office", "city": "Hamilton", "timezone": "America/Toronto"}


@pytest.fixture
def session():
    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = MagicMock()
    return session


@pytest.fixture
def client(session):
    app = create_app(Settings(_env_file=None, environment="test"))

    async def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_user] = lambda: User(role="admin")
    with TestClient(app) as client:
        yield client


def test_crud_response_contract(client, session):
    site = Site(**VALUES)
    session.execute.return_value.scalars.return_value.first.return_value = site
    session.execute.return_value.scalars.return_value.all.return_value = [site]
    created = client.post("/api/v1/sites", json=VALUES)
    assert created.status_code == 201
    assert set(created.json()) == {"id", "name", "city", "timezone", "active"}
    session.commit.assert_awaited_once()
    assert client.get(f"/api/v1/sites/{site.id}").json()["id"] == str(site.id)
    assert client.get("/api/v1/sites?active=true").json()[0]["id"] == str(site.id)
    updated = client.patch(f"/api/v1/sites/{site.id}", json={"active": False})
    assert updated.status_code == 200
    assert updated.json()["active"] is False
    deleted = client.delete(f"/api/v1/sites/{site.id}")
    assert deleted.status_code == 204
    assert deleted.content == b""
    session.delete.assert_awaited_once_with(site)


def test_missing_and_malformed_input(client, session):
    session.execute.return_value.scalars.return_value.first.return_value = None
    for method, body in (("get", None), ("patch", {"active": False}), ("delete", None)):
        kwargs = {} if body is None else {"json": body}
        assert client.request(method, f"/api/v1/sites/{uuid4()}", **kwargs).status_code == 404
        assert client.request(method, "/api/v1/sites/not-a-uuid", **kwargs).status_code == 422
    assert client.post("/api/v1/sites", json={}).status_code == 422
    assert client.patch(f"/api/v1/sites/{uuid4()}", json={}).status_code == 422
    assert client.get("/api/v1/sites?active=invalid").status_code == 422
    session.commit.assert_not_awaited()


@pytest.mark.parametrize("active", [None, True, False])
async def test_filter_is_applied_in_sql(session, active):
    await SiteService().get_all_sites(session, active)
    statement = session.execute.call_args.args[0]
    sql = str(statement).lower()
    assert ("where" in sql) == (active is not None)
    if active is not None:
        assert f"site.active = {str(active).lower()}" in sql


@pytest.mark.parametrize("operation", ["create", "update", "delete"])
async def test_failed_writes_rollback(session, operation):
    site = Site(**VALUES)
    session.execute.return_value.scalars.return_value.first.return_value = site
    session.commit.side_effect = RuntimeError("write failed")
    service = SiteService()
    with pytest.raises(RuntimeError, match="write failed"):
        if operation == "create":
            await service.create_site(SiteCreate(**VALUES), session)
        elif operation == "update":
            await service.update_site(site.id, SiteUpdate(active=False), session)
        else:
            await service.delete_site(site.id, session)
    session.rollback.assert_awaited_once()
