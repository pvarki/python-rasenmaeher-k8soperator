import asyncio
import base64

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from cloudcoil.models.kubernetes.core.v1 import Secret
from cloudcoil.errors import ResourceNotFound

from api.config import config
from api.lib.certificates.pfx import build_pfx
from api.routes.certificates.schema import PFX_MEDIA_TYPE, PFX_RESPONSES, Callsign
from k8soperator.controllers._certificates import EXTERNAL_CERT_NAMESPACE, secret_name
from k8soperator.models.v1alpha1.user import User


router = APIRouter(prefix="/certificates", tags=["certificates"])

CERTIFICATE_NOT_ISSUED_MESSAGE = "Certificate not issued yet."
USER_NOT_FOUND_MESSAGE = "User {callsign} not found."


@router.get("/{callsign}.pfx", response_class=Response, responses=PFX_RESPONSES)
async def get_user_pfx(
    callsign: Callsign,
) -> Response:
    """Retrieve user certificate in the form .pfx"""
    try:
        user = await User.async_get(name=callsign)
    except ResourceNotFound:
        raise HTTPException(404, detail=USER_NOT_FOUND_MESSAGE.format(callsign=callsign))
    try:
        secret = await Secret.async_get(secret_name(user), EXTERNAL_CERT_NAMESPACE)
    except ResourceNotFound:
        raise HTTPException(409, detail=CERTIFICATE_NOT_ISSUED_MESSAGE)
    data = secret.data or {}
    if "tls.key" not in data or "tls.crt" not in data:
        raise HTTPException(409, detail=CERTIFICATE_NOT_ISSUED_MESSAGE)
    return Response(
        content=await asyncio.to_thread(
            build_pfx, user.spec.callsign, base64.b64decode(data["tls.key"]), base64.b64decode(data["tls.crt"])
        ),
        media_type=PFX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{user.spec.callsign}_{config.deployment}.pfx"'},
    )
