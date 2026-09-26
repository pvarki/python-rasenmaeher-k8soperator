"""Enrollment endpoints."""

from fastapi import APIRouter, HTTPException, status

from api.lib.common.invites import CallsignTaken, InvalidCallsign, InviteNotRedeemable, find_invite, redeem
from api.lib.common.jwt import issue
from api.routes.enrollment.schema import CheckRequest, CheckResponse, EnrollmentStatus, EnrollRequest, EnrollResponse

router = APIRouter(prefix="/enrollment", tags=["enrollment"])


@router.post("/check")
async def check(request: CheckRequest) -> CheckResponse:
    """Check an invite code before asking for a callsign.

    Nothing is reserved, so another user may take the last use before this one creates their user.
    """
    return CheckResponse(valid=await find_invite(request.code) is not None)


@router.post("", status_code=status.HTTP_201_CREATED)
async def enroll(request: EnrollRequest) -> EnrollResponse:
    """Redeem an invite code as a new user."""
    try:
        user = await redeem(request.code, request.callsign)
    except InviteNotRedeemable as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND) from exc
    except CallsignTaken as exc:
        raise HTTPException(status.HTTP_409_CONFLICT) from exc
    except InvalidCallsign as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT) from exc
    return EnrollResponse(status=EnrollmentStatus.from_resource(user), token=issue(user))
