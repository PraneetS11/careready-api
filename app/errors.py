from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class SiteNotFound(Exception):
    """The requested site does not exist."""


def register_error_handlers(app: FastAPI):
    async def site_not_found(request: Request, exc: SiteNotFound):
        return JSONResponse(
            status_code=404, content={"message": "Site not found", "error_code": "site_not_found"}
        )

    app.add_exception_handler(SiteNotFound, site_not_found)
