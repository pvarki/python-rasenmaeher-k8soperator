"""Role controller: report Ready for catalog roles."""

from cloudcoil.controller import Context, Controller

from rmk8soperator.controllers._refs import mark_resolved
from rmk8soperator.models.v1alpha1 import Role

roles = Controller(Role, name="roles")


@roles.reconcile()
async def reconcile_role(role: Role, ctx: Context[Role]) -> None:
    """Roles have no outgoing refs; mark them resolved."""
    mark_resolved(ctx)
