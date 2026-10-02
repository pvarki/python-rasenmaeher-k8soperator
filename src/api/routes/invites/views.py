"""Invite endpoints."""

from fastapi import APIRouter, HTTPException, status

from api.lib.common.invites import create_invite, get_invite, list_invites, unique_invite_code
from api.routes.invites.schema import CreateInviteRequest, InviteResponse

# TODO: admin auth
router = APIRouter(prefix="/invites", tags=["invites"])


@router.get("")
async def read_invites() -> list[InviteResponse]:
    """All invites, except auto-approving ones."""
    invites = await list_invites()
    return InviteResponse.from_resources(invites)


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_invite(request: CreateInviteRequest) -> InviteResponse:
    """Create an invite with a generated code."""
    code = await unique_invite_code()
    invite = await create_invite(request.to_spec(code))
    return InviteResponse.from_resource(invite)


@router.get("/{code}")
async def read_invite(code: str) -> InviteResponse:
    """Invite with the code."""
    invite = await get_invite(code)
    if invite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return InviteResponse.from_resource(invite)
