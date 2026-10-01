import logging
from time import perf_counter

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

logger = logging.getLogger("careready.requests")
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())


class RequestLoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        started = perf_counter()
        status_code = 500

        async def record_status(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, record_status)
        finally:
            # Route templates hide token-bearing path parameters. Never log raw
            # URLs, query strings, request bodies, cookies or authorization.
            route = scope.get("route")
            path = getattr(route, "path", "<unmatched>")
            logger.info(
                "method=%s path=%s status=%s elapsed_ms=%.2f",
                scope["method"],
                path,
                status_code,
                (perf_counter() - started) * 1000,
            )


def register_middleware(app, settings):
    hosts = list(settings.allowed_hosts)
    if settings.environment == "test" and "testserver" not in hosts:
        hosts.append("testserver")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)
    app.add_middleware(RequestLoggingMiddleware)
    # Uvicorn's access logger includes raw query strings; use the safe logger above.
    logging.getLogger("uvicorn.access").disabled = True
