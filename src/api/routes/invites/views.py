"""Invite endpoints."""

from fastapi import APIRouter, HTTPException, status

from cloudcoil.errors import ResourceConflict

from api.lib.common.invites import (
    create_invite,
    delete_invite,
    get_invite,
    list_invites,
    unique_invite_code,
    update_invite,
)
from api.routes.invites.schema import CreateInviteRequest, InviteResponse, UpdateInviteRequest

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


@router.patch("/{code}")
async def patch_invite(code: str, request: UpdateInviteRequest) -> InviteResponse:
    """Change the sent fields of the invite, validUntil null for no expiration."""
    invite = await get_invite(code)
    if invite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    spec = request.apply(invite.spec)
    try:
        invite = await update_invite(invite, spec)
    except ResourceConflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT) from exc
    return InviteResponse.from_resource(invite)


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_invite(code: str) -> None:
    """Delete the invite."""
    invite = await get_invite(code)
    if invite is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    await delete_invite(invite)
