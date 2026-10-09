"""FastAPI application, run with `uvicorn rmapi.app:app`"""

from fastapi import APIRouter, FastAPI

from api import __version__
from api.config import config
from api.routes.certificates.views import router as certificates_router
from api.routes.enrollment.views import router as enrollment_router
from api.routes.invites.views import router as invites_router


app = FastAPI(
    title="rmapi",
    version=__version__,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)

v3 = APIRouter(prefix="/api/v3")
v3.include_router(certificates_router)
v3.include_router(enrollment_router)
v3.include_router(invites_router)
app.include_router(v3)


# TODO: Remove, for testing UI <-> API communication
@app.get("/api/v3/healthcheck")
async def healthcheck() -> dict[str, str]:
    """Are we running at all"""
    return {"dns": config.dns, "version": __version__, "deployment": config.dns.split(".")[0]}
