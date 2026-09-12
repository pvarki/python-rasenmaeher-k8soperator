"""Reference helpers and reconcile handlers."""

from typing import cast

import pytest
from cloudcoil.apimachinery import ObjectMeta
from cloudcoil.controller import Context, ResourceKey, TerminalError, Wait

from rmk8soperator.controllers._refs import referrers_of, resolve_refs
from rmk8soperator.controllers.groups import reconcile_group
from rmk8soperator.controllers.invites import reconcile_invite
from rmk8soperator.controllers.roles import reconcile_role
from rmk8soperator.controllers.users import reconcile_user
from rmk8soperator.models.v1alpha1 import (
    API_VERSION,
    Group,
    GroupSpec,
    Invite,
    InviteSpec,
    ObjectRef,
    Role,
    RoleSpec,
    User,
    UserSpec,
)
from tests.conftest import FakeCache, FakeContext


def _user(name: str, *, roles: list[str] | None = None, groups: list[str] | None = None) -> User:
    return User(
        api_version=API_VERSION,
        kind="User",
        metadata=ObjectMeta(name=name, uid=f"uid-{name}"),
        spec=UserSpec(
            callsign=name,
            public_key="ssh-ed25519 AAAA",
            role_refs=[ObjectRef(name=item) for item in roles or []],
            group_refs=[ObjectRef(name=item) for item in groups or []],
        ),
    )


def _role(name: str) -> Role:
    return Role(
        api_version=API_VERSION,
        kind="Role",
        metadata=ObjectMeta(name=name, uid=f"uid-{name}"),
        spec=RoleSpec(name=name, display_name=name),
    )


def _group(
    name: str,
    *,
    parent: str | None = None,
    managers: list[str] | None = None,
    roles: list[str] | None = None,
) -> Group:
    return Group(
        api_version=API_VERSION,
        kind="Group",
        metadata=ObjectMeta(name=name, uid=f"uid-{name}"),
        spec=GroupSpec(
            name=name,
            display_name=name,
            parent_ref=ObjectRef(name=parent) if parent else None,
            manager_refs=[ObjectRef(name=item) for item in managers or []],
            role_refs=[ObjectRef(name=item) for item in roles or []],
        ),
    )


def _invite(name: str, *, groups: list[str] | None = None, roles: list[str] | None = None) -> Invite:
    return Invite(
        api_version=API_VERSION,
        kind="Invite",
        metadata=ObjectMeta(name=name, uid=f"uid-{name}"),
        spec=InviteSpec(
            code="invite-code",
            group_refs=[ObjectRef(name=item) for item in groups or []],
            role_refs=[ObjectRef(name=item) for item in roles or []],
        ),
    )


@pytest.mark.asyncio
async def test_reconcile_user_resolves_refs() -> None:
    """User status receives UIDs for named roles and groups."""
    role = _role("superadmin")
    group = _group("ops")
    ctx = FakeContext(
        {
            Role: FakeCache({"superadmin": role}),
            Group: FakeCache({"ops": group}),
        }
    )
    user = _user("alice", roles=["superadmin"], groups=["ops"])
    await reconcile_user(user, cast(Context[User], ctx))
    assert ctx.status["roles"][0].uid == "uid-superadmin"
    assert ctx.status["groups"][0].uid == "uid-ops"
    assert ctx.conditions[-1] == ("ReferencesResolved", True, "Resolved", "")


@pytest.mark.asyncio
async def test_reconcile_user_waits_for_missing_role() -> None:
    """Missing role refs wait instead of failing."""
    ctx = FakeContext({Role: FakeCache(), Group: FakeCache()})
    user = _user("alice", roles=["missing"])
    with pytest.raises(Wait) as raised:
        await reconcile_user(user, cast(Context[User], ctx))
    assert raised.value.reason == "MissingReference"
    assert ctx.conditions[0][1] is False
    assert ctx.conditions[0][2] == "MissingReference"


@pytest.mark.asyncio
async def test_reconcile_group_and_invite() -> None:
    """Group reports references while Invite validates its references."""
    parent = _group("root")
    manager = _user("alice")
    role = _role("group-admin")
    ctx = FakeContext(
        {
            Group: FakeCache({"root": parent}),
            User: FakeCache({"alice": manager}),
            Role: FakeCache({"group-admin": role}),
        }
    )
    group = _group("ops", parent="root", managers=["alice"], roles=["group-admin"])
    await reconcile_group(group, cast(Context[Group], ctx))
    assert ctx.status["parent"].uid == "uid-root"
    assert ctx.status["managers"][0].uid == "uid-alice"
    assert ctx.status["roles"][0].uid == "uid-group-admin"

    invite_ctx = FakeContext(
        {
            Group: FakeCache({"root": parent}),
            Role: FakeCache({"group-admin": role}),
        }
    )
    invite = _invite("onboarding", groups=["root"], roles=["group-admin"])
    await reconcile_invite(invite, cast(Context[Invite], invite_ctx))
    assert invite_ctx.status == {}
    assert invite_ctx.conditions[-1] == ("ReferencesResolved", True, "Resolved", "")


@pytest.mark.asyncio
async def test_reconcile_group_rejects_self_parent() -> None:
    """A group may not name itself as parent."""
    ctx = FakeContext()
    group = _group("ops", parent="ops")
    with pytest.raises(TerminalError):
        await reconcile_group(group, cast(Context[Group], ctx))
    assert ctx.conditions[0][2] == "SelfReference"


@pytest.mark.asyncio
async def test_reconcile_group_rejects_parent_cycle() -> None:
    """A two-node parent loop is a permanent reconcile failure."""
    eng = _group("eng", parent="ops")
    ctx = FakeContext({Group: FakeCache({"eng": eng})})
    group = _group("ops", parent="eng")
    with pytest.raises(TerminalError):
        await reconcile_group(group, cast(Context[Group], ctx))
    assert ctx.conditions[0][2] == "CycleDetected"
    assert "ops -> eng -> ops" in ctx.conditions[0][3]


@pytest.mark.asyncio
async def test_reconcile_group_waits_for_missing_ancestor() -> None:
    """A missing ancestor waits instead of resolving the immediate parent."""
    eng = _group("eng", parent="missing")
    ctx = FakeContext({Group: FakeCache({"eng": eng})})
    group = _group("ops", parent="eng")
    with pytest.raises(Wait) as raised:
        await reconcile_group(group, cast(Context[Group], ctx))
    assert raised.value.reason == "MissingReference"
    assert ctx.conditions[0][2] == "MissingReference"


@pytest.mark.asyncio
async def test_reconcile_role_marks_resolved() -> None:
    """Roles have no outgoing refs and report ReferencesResolved."""
    ctx = FakeContext()
    role = _role("superadmin")
    await reconcile_role(role, cast(Context[Role], ctx))
    assert ctx.conditions[-1] == ("ReferencesResolved", True, "Resolved", "")


def test_referrers_of_matches_name_refs() -> None:
    """Reverse mapping finds objects that name the target."""
    alice = _user("alice", roles=["superadmin"])
    bob = _user("bob", roles=["group-admin"])
    target = _role("superadmin")
    keys = referrers_of([alice, bob], lambda user: user.spec.role_refs, target)
    assert keys == [ResourceKey("alice")]


def test_resolve_refs_skips_objects_without_uid() -> None:
    """A cached object without a UID is treated as missing."""
    role = Role(
        api_version=API_VERSION,
        kind="Role",
        metadata=ObjectMeta(name="superadmin"),
        spec=RoleSpec(name="superadmin", display_name="Superadmin"),
    )
    ctx = FakeContext({Role: FakeCache({"superadmin": role})})
    with pytest.raises(Wait):
        resolve_refs(ctx, Role, [ObjectRef(name="superadmin")])
