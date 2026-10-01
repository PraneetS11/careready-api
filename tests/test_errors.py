from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.config import Settings
from app.db.session import get_session
from app.main import create_app
from app.models.users import User


@pytest.mark.parametrize(
    "method,body", [("GET", None), ("PATCH", {"active": False}), ("DELETE", None)]
)
def test_missing_site_has_stable_safe_error(method, body):
    app = create_app(Settings(_env_file=None, environment="test"))
    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = MagicMock()
    session.execute.return_value.scalars.return_value.first.return_value = None

    async def override():
        yield session

    app.dependency_overrides[get_session] = override
    app.dependency_overrides[get_current_user] = lambda: User(role="admin")
    with TestClient(app) as client:
        kwargs = {} if body is None else {"json": body}
        response = client.request(method, f"/api/v1/sites/{uuid4()}", **kwargs)
        assert response.status_code == 404
        assert response.json() == {"message": "Site not found", "error_code": "site_not_found"}
        assert client.request(method, "/api/v1/sites/not-a-uuid", **kwargs).status_code == 422
    session.commit.assert_not_awaited()
