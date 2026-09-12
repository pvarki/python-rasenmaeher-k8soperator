"""User controller: resolve role and group name refs into status."""

from cloudcoil.controller import Context, Controller, ResourceKey

from rmk8soperator.controllers._refs import mark_resolved, referrers_of, resolve_refs
from rmk8soperator.models.v1alpha1 import Group, Role, User

users = Controller(User, name="users")


@users.reconcile()
async def reconcile_user(user: User, ctx: Context[User]) -> None:
    """Write resolved role and group UIDs, waiting for missing targets."""
    roles = resolve_refs(ctx, Role, user.spec.role_refs)
    groups = resolve_refs(ctx, Group, user.spec.group_refs)
    mark_resolved(ctx)
    ctx.set_status(roles=roles, groups=groups)


@users.watch(Role)
def role_changed(role: Role) -> list[ResourceKey]:
    """Requeue users that name this role."""
    return referrers_of(users.cached(User).list(), lambda obj: obj.spec.role_refs, role)


@users.watch(Group)
def group_changed(group: Group) -> list[ResourceKey]:
    """Requeue users that name this group."""
    return referrers_of(users.cached(User).list(), lambda obj: obj.spec.group_refs, group)
