"""Managing invites and redeeming them into users."""

from datetime import UTC, datetime
from cloudcoil.apimachinery import ObjectMeta
from cloudcoil.controller import get_condition
from cloudcoil.errors import ResourceConflict

from api.lib.common.codes import generate_code
from k8soperator.models.v1alpha1.common import API_VERSION
from k8soperator.models.v1alpha1.invite import Invite, InviteStatus
from k8soperator.models.v1alpha1.user import User, UserSpec

APPROVAL_CODE_LENGTH = 8
UNLIMITED = -1


class InviteNotRedeemable(Exception):
    """No invite with the code, or it is not ready, expired or used up"""


class CallsignTaken(Exception):
    """A user with the callsign already exists"""


async def get_invite(code: str, include_auto_approve: bool = False) -> Invite | None:
    """Invite with the code in any state, auto-approving ones only if included."""
    # TODO: A better way to do this?
    async for invite in await Invite.async_list():
        if invite.spec.code != code:
            continue
        if invite.spec.auto_approve and not include_auto_approve:
            return None
        return invite
    return None


async def find_invite(code: str) -> Invite | None:
    """Invite with the code, if it can still be redeemed."""
    invite = await get_invite(code, include_auto_approve=True)
    return invite if invite is not None and is_redeemable(invite) else None


async def list_invites() -> list[Invite]:
    """Invites in any state, except auto-approving ones."""
    invites = []
    async for invite in await Invite.async_list():
        if not invite.spec.auto_approve:
            invites.append(invite)
    return invites


async def redeem(code: str, callsign: str) -> User:
    """Create a user from the invite code, using one use of the invite."""
    invite = await find_invite(code)
    if invite is None:
        raise InviteNotRedeemable
    user = _new_user(invite, callsign)
    await _check_callsign(user)
    await _use(invite)
    return await user.async_create()


def used_count(invite: Invite) -> int:
    """Times the invite has been redeemed."""
    return invite.status.used if invite.status else 0


def _is_ready(invite: Invite) -> bool:
    ready = get_condition(invite, "ReferencesResolved")
    return ready is not None and ready.status == "True"


def is_redeemable(invite: Invite) -> bool:
    """Whether the invite is ready, not expired and not used up."""
    expired = invite.spec.valid_until is not None and invite.spec.valid_until <= datetime.now(UTC)
    used_up = invite.spec.use_count != UNLIMITED and used_count(invite) >= invite.spec.use_count
    return _is_ready(invite) and not expired and not used_up


def _new_user(invite: Invite, callsign: str) -> User:
    return User(
        api_version=API_VERSION,
        kind="User",
        metadata=ObjectMeta(name=callsign),
        spec=UserSpec(
            callsign=callsign,
            role_refs=invite.spec.role_refs,
            group_refs=invite.spec.group_refs,
            approval_code=generate_code(APPROVAL_CODE_LENGTH),
            approved_at=datetime.now(UTC) if invite.spec.auto_approve else None,
        ),
    )


async def _check_callsign(user: User) -> None:
    """Fail on a taken callsign before the invite is used."""
    try:
        await user.async_create(dry_run=True)
    except ResourceConflict as exc:
        raise CallsignTaken from exc


async def _use(invite: Invite) -> None:
    invite.status = invite.status or InviteStatus()
    invite.status.used += 1
    try:
        await invite.async_update_status()
    except ResourceConflict as exc:
        raise InviteNotRedeemable from exc  # Invite changed since it was read
