from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api import site_data
from app.core.config import Settings
from app.main import create_app
from app.models.sites import Site
from app.schemas.sites import SiteCreate, SiteRead, SiteUpdate


def test_site_identity_and_schema_boundary():
    values = {"name": "Test office", "city": "Hamilton", "timezone": "America/Toronto"}
    first, second = Site(**values), Site(**values)
    assert isinstance(first.id, UUID)
    assert first.id != second.id
    assert first.active is True
    assert "id" not in SiteCreate.model_fields
    assert SiteRead.model_validate(first).id == first.id
    with pytest.raises(ValidationError):
        SiteRead(**values)
    assert SiteUpdate(active=False).model_dump() == {"active": False}


def test_chapter4_in_memory_crud_is_preserved(monkeypatch):
    monkeypatch.setattr(site_data, "sites", [])
    monkeypatch.setattr(site_data, "next_id", 1)
    with TestClient(create_app(Settings(_env_file=None, environment="test"))) as client:
        created = client.post(
            "/api/v1/sites",
            json={"name": "Test", "city": "Hamilton", "timezone": "America/Toronto"},
        )
        assert created.status_code == 201
        assert created.json()["id"] == 1
        assert client.get("/api/v1/sites/1").json() == created.json()
        assert client.patch("/api/v1/sites/1", json={"active": False}).json()["active"] is False
        assert client.get("/api/v1/sites?active=true").json() == []
        assert len(client.get("/api/v1/sites?active=false").json()) == 1
        assert client.delete("/api/v1/sites/1").status_code == 204
        assert client.get("/api/v1/sites/1").status_code == 404
