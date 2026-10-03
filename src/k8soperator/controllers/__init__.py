"""Controller groups included by the platform operator."""

from typing import Any

from cloudcoil.controller import Controller

from k8soperator.controllers.groups import groups
from k8soperator.controllers.invites import invites
from k8soperator.controllers.roles import roles
from k8soperator.controllers.users import users

ALL_CONTROLLERS: tuple[Controller[Any], ...] = (users, groups, roles, invites)

__all__ = ["ALL_CONTROLLERS", "groups", "invites", "roles", "users"]
