from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_liveness_is_independent_of_services():
    with TestClient(create_app(Settings(_env_file=None, environment="test"))) as client:
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert "/health/ready" in client.get("/openapi.json").json()["paths"]
        assert client.get("/unknown").status_code == 404


@pytest.mark.parametrize(
    "database,redis,expected",
    [
        ("ok", "ok", 200),
        ("unavailable", "ok", 503),
        ("ok", "unavailable", 503),
    ],
)
def test_readiness_reports_dependency_outages(database, redis, expected):
    with TestClient(create_app(Settings(_env_file=None, environment="test"))) as client:
        with patch(
            "app.api.health.check_dependencies",
            new=AsyncMock(return_value={"database": database, "redis": redis}),
        ):
            response = client.get("/health/ready")
        assert response.status_code == expected
        assert response.json()["checks"] == {"database": database, "redis": redis}


def test_settings_are_environment_driven(monkeypatch):
    monkeypatch.setenv("APP_NAME", "Isolated Test API")
    assert Settings(_env_file=None).app_name == "Isolated Test API"


def test_readiness_handles_real_client_failures_without_leaking_secrets():
    with TestClient(create_app(Settings(_env_file=None, environment="test"))) as client:
        with patch.object(
            type(client.app.state.engine), "connect", side_effect=RuntimeError("secret")
        ):
            with patch.object(
                client.app.state.redis, "ping", new=AsyncMock(side_effect=RuntimeError("secret"))
            ):
                response = client.get("/health/ready")
        assert response.status_code == 503
        assert "secret" not in response.text
