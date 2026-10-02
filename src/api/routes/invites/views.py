"""Invite endpoints."""

from fastapi import APIRouter, HTTPException, status

from api.lib.common.invites import get_invite, list_invites
from api.routes.invites.schema import InviteResponse

# TODO: admin auth
router = APIRouter(prefix="/invites", tags=["invites"])


@router.get("")
async def read_invites() -> list[InviteResponse]:
    """All invites, except auto-approving ones."""
    invites = await list_invites()
    return InviteResponse.from_resources(invites)


@router.get("/{code}")
async def read_invite(code: str) -> InviteResponse:
    """Invite with the code."""
    invite = await get_invite(code)
    if invite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return InviteResponse.from_resource(invite)
