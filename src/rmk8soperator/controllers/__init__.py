"""Controller groups included by the platform operator."""

from typing import Any

from cloudcoil.controller import Controller

from rmk8soperator.controllers.groups import groups
from rmk8soperator.controllers.invites import invites
from rmk8soperator.controllers.roles import roles
from rmk8soperator.controllers.users import users

ALL_CONTROLLERS: tuple[Controller[Any], ...] = (users, groups, roles, invites)

__all__ = ["ALL_CONTROLLERS", "groups", "invites", "roles", "users"]
