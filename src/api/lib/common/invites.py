"""Redeeming invites into users."""

from datetime import UTC, datetime
from http import HTTPStatus

from cloudcoil.apimachinery import ObjectMeta
from cloudcoil.errors import APIError, ResourceConflict

from api.lib.common.codes import generate_code
from k8soperator.models.v1alpha1.common import API_VERSION
from k8soperator.models.v1alpha1.invite import Invite
from k8soperator.models.v1alpha1.user import User, UserSpec

APPROVAL_CODE_LENGTH = 8
UNLIMITED = -1


class InviteNotRedeemable(Exception):
    """No invite with the code, or it is expired or used up"""


class CallsignTaken(Exception):
    """A user with the callsign already exists"""


class InvalidCallsign(Exception):
    """The callsign is not a valid user name"""


async def find_invite(code: str) -> Invite | None:
    """Invite with the code, if it can still be redeemed."""
    # TODO: A better way to do this?
    async for invite in await Invite.async_list():
        if invite.spec.code == code and _is_redeemable(invite):
            return invite
    return None


async def redeem(code: str, callsign: str) -> User:
    """Create a user from the invite code, using one use of the invite."""
    invite = await find_invite(code)
    if invite is None:
        raise InviteNotRedeemable
    user = _new_user(invite, callsign)
    await _check_callsign(user)
    await _use(invite)
    return await user.async_create()


def _used(invite: Invite) -> int:
    return invite.status.used if invite.status else 0


def _is_redeemable(invite: Invite) -> bool:
    expired = invite.spec.valid_until is not None and invite.spec.valid_until <= datetime.now(UTC)
    used_up = invite.spec.use_count != UNLIMITED and _used(invite) >= invite.spec.use_count
    return not expired and not used_up


def _new_user(invite: Invite, callsign: str) -> User:
    assert invite.name is not None
    return User(
        api_version=API_VERSION,
        kind="User",
        metadata=ObjectMeta(name=callsign.lower()),
        spec=UserSpec(
            callsign=callsign,
            role_refs=invite.spec.role_refs,
            group_refs=invite.spec.group_refs,
            approval_code=generate_code(APPROVAL_CODE_LENGTH),
            approved_at=datetime.now(UTC) if invite.spec.auto_approve else None,
        ),
    )


async def _check_callsign(user: User) -> None:
    """Fail on a taken or invalid callsign before the invite is used."""
    try:
        await user.async_create(dry_run=True)
    except ResourceConflict as exc:
        raise CallsignTaken from exc
    except APIError as exc:
        if exc.status_code != HTTPStatus.UNPROCESSABLE_ENTITY:
            raise
        raise InvalidCallsign from exc


async def _use(invite: Invite) -> None:
    used = _used(invite)
    try:
        await invite.async_patch(
            [
                {"op": "test", "path": "/status/used", "value": used},
                {"op": "replace", "path": "/status/used", "value": used + 1},
            ],
            subresource="status",
        )
    except APIError as exc: # Other user got here first
        raise InviteNotRedeemable from exc
