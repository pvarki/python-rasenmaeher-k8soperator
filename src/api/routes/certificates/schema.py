"""Request and response schemas for the certificates routes."""

from typing import Annotated, Any

from fastapi import Path
from pydantic import BaseModel

PFX_MEDIA_TYPE = "application/x-pkcs12"

Callsign = Annotated[str, Path(pattern=r"^[a-z0-9]{3,30}$", description="Callsign of the user.")]


class ErrorResponse(BaseModel):
    """Error body, same shape as FastAPI's HTTPException."""

    detail: str


PFX_RESPONSES: dict[int | str, dict[str, Any]] = {
    200: {"content": {PFX_MEDIA_TYPE: {}}, "description": "PKCS#12 bundle."},
    404: {"model": ErrorResponse, "description": "User not found."},
    409: {"model": ErrorResponse, "description": "Certificate not issued yet."},
}
