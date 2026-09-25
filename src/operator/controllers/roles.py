"""Role controller: report Ready for catalog roles."""

from cloudcoil.controller import Context, Controller

from operator.controllers._events import recorder
from operator.controllers._refs import mark_resolved
from operator.models.v1alpha1 import Role

roles = Controller(Role, name="roles", events=recorder("roles"))


@roles.reconcile()
async def reconcile_role(role: Role, ctx: Context[Role]) -> None:
    """Roles have no outgoing refs; mark them resolved."""
    mark_resolved(ctx)
