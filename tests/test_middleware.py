import unittest
from types import SimpleNamespace

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.middleware import register_middleware


class MiddlewareTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        register_middleware(
            app,
            SimpleNamespace(
                environment="test",
                allowed_hosts=["localhost", "127.0.0.1"],
                cors_origins=["http://localhost:3000"],
            ),
        )

        @app.get("/ok")
        def ok():
            return {"ok": True}

        @app.get("/missing/{record_id}")
        def missing(record_id: str):
            raise HTTPException(404, "Missing")

        @app.get("/verify/{token}")
        def verify(token: str):
            return {"ok": True}

        @app.get("/crash")
        def crash():
            raise RuntimeError("must-not-be-logged")

        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_logs_success_and_handled_error_without_secrets(self):
        with self.assertLogs("careready.requests", level="INFO") as logs:
            response = self.client.get(
                "/ok?token=secret-query", headers={"Authorization": "Bearer secret-header"}
            )
            missing = self.client.get("/missing/private-id")
            self.client.get("/verify/secret-path")
        self.assertEqual(response.json(), {"ok": True})
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json(), {"detail": "Missing"})
        text = " ".join(logs.output)
        for expected in [
            "method=GET",
            "path=/ok",
            "status=200",
            "status=404",
            "elapsed_ms=",
            "/verify/{token}",
        ]:
            self.assertIn(expected, text)
        for secret in ["secret-query", "secret-header", "secret-path", "private-id"]:
            self.assertNotIn(secret, text)

    def test_cors_and_host_policy(self):
        allowed = self.client.get("/ok", headers={"Origin": "http://localhost:3000"})
        self.assertEqual(allowed.headers["access-control-allow-origin"], "http://localhost:3000")
        denied = self.client.get("/ok", headers={"Origin": "https://unlisted.example"})
        self.assertNotIn("access-control-allow-origin", denied.headers)
        preflight = self.client.options(
            "/ok",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        self.assertEqual(preflight.status_code, 200)
        self.assertEqual(
            self.client.get("/ok", headers={"Host": "untrusted.example"}).status_code, 400
        )
        self.assertEqual(self.client.get("/docs").status_code, 200)

    def test_unhandled_error_is_logged_and_not_swallowed(self):
        with self.assertLogs("careready.requests", level="INFO") as logs:
            with self.assertRaises(RuntimeError):
                self.client.get("/crash")
        self.assertIn("status=500", " ".join(logs.output))
        self.assertNotIn("must-not-be-logged", " ".join(logs.output))
