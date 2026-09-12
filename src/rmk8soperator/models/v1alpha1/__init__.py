"""platform.opendefence.fi/v1alpha1 resources."""

from rmk8soperator.models.v1alpha1.common import API_VERSION, ObjectRef, PlatformStatus, ResolvedRef
from rmk8soperator.models.v1alpha1.group import Group, GroupSpec, GroupStatus
from rmk8soperator.models.v1alpha1.invite import Invite, InviteSpec, InviteStatus
from rmk8soperator.models.v1alpha1.role import Role, RoleSpec, RoleStatus
from rmk8soperator.models.v1alpha1.user import User, UserSpec, UserStatus

__all__ = [
    "API_VERSION",
    "Group",
    "GroupSpec",
    "GroupStatus",
    "Invite",
    "InviteSpec",
    "InviteStatus",
    "ObjectRef",
    "PlatformStatus",
    "ResolvedRef",
    "Role",
    "RoleSpec",
    "RoleStatus",
    "User",
    "UserSpec",
    "UserStatus",
]
