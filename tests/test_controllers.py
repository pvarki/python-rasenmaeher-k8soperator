"""Reference helpers and reconcile handlers."""

from collections.abc import Callable
from typing import Any, cast
from unittest.mock import Mock, PropertyMock

import pytest
from cloudcoil.apimachinery import ObjectMeta
from cloudcoil.controller import Context, Controller, ResourceKey, TerminalError, Wait
from cloudcoil.resources import Resource

from rmk8soperator.controllers import groups, invites, users
from rmk8soperator.controllers._refs import referrers_of, resolve_refs
from rmk8soperator.controllers.groups import manager_changed, parent_group_changed, reconcile_group
from rmk8soperator.controllers.groups import role_changed as group_role_changed
from rmk8soperator.controllers.invites import group_changed as invite_group_changed
from rmk8soperator.controllers.invites import reconcile_invite
from rmk8soperator.controllers.invites import role_changed as invite_role_changed
from rmk8soperator.controllers.roles import reconcile_role
from rmk8soperator.controllers.users import group_changed as user_group_changed
from rmk8soperator.controllers.users import reconcile_user
from rmk8soperator.controllers.users import role_changed as user_role_changed
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


@pytest.mark.parametrize(
    ("controller", "mapper", "primary", "target"),
    [
        (groups, parent_group_changed, _group("dependent", parent="target"), _group("target")),
        (groups, manager_changed, _group("dependent", managers=["target"]), _user("target")),
        (groups, group_role_changed, _group("dependent", roles=["target"]), _role("target")),
        (users, user_group_changed, _user("dependent", groups=["target"]), _group("target")),
        (users, user_role_changed, _user("dependent", roles=["target"]), _role("target")),
        (invites, invite_group_changed, _invite("dependent", groups=["target"]), _group("target")),
        (invites, invite_role_changed, _invite("dependent", roles=["target"]), _role("target")),
    ],
)
def test_watch_mappers_wait_for_initial_sync(
    monkeypatch: pytest.MonkeyPatch,
    controller: Controller[Any],
    mapper: Callable[[Any], list[ResourceKey]],
    primary: Resource,
    target: Resource,
) -> None:
    """Initial list events must not read unsynced snapshots; later events requeue dependents."""
    ready = PropertyMock(return_value=False)
    monkeypatch.setattr(Controller, "ready", ready)
    cache = Mock()
    cache.list.return_value = [primary]
    cached = Mock(return_value=cache)
    monkeypatch.setattr(controller, "cached", cached)

    assert mapper(target) == []
    cached.assert_not_called()

    ready.return_value = True
    assert mapper(target) == [ResourceKey("dependent")]
    cached.assert_called_once_with(type(primary))

    cache.list.side_effect = RuntimeError("Informer watch failed")
    with pytest.raises(RuntimeError, match="Informer watch failed"):
        mapper(target)


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
