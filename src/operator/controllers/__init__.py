"""Controller groups included by the platform operator."""

from typing import Any

from cloudcoil.controller import Controller

from operator.controllers.groups import groups
from operator.controllers.invites import invites
from operator.controllers.roles import roles
from operator.controllers.users import users

ALL_CONTROLLERS: tuple[Controller[Any], ...] = (users, groups, roles, invites)

__all__ = ["ALL_CONTROLLERS", "groups", "invites", "roles", "users"]
