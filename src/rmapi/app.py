"""FastAPI application, run with `uvicorn rmapi.app:app`"""

from fastapi import FastAPI

from rmapi import __version__
from rmapi.config import config

app = FastAPI(title="rmapi", version=__version__)


# TODO: Remove, for testing UI <-> API communication
@app.get("/api/v1/healthcheck")
async def healthcheck() -> dict[str, str]:
    """Are we running at all"""
    return {"dns": config.dns, "version": __version__, "deployment": config.dns.split(".")[0]}
