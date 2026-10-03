"""platform.opendefence.fi/v1alpha1 resources."""

from k8soperator.models.v1alpha1.common import API_VERSION, ObjectRef, PlatformStatus, ResolvedRef
from k8soperator.models.v1alpha1.group import Group, GroupSpec, GroupStatus
from k8soperator.models.v1alpha1.invite import Invite, InviteSpec, InviteStatus
from k8soperator.models.v1alpha1.role import Role, RoleSpec, RoleStatus
from k8soperator.models.v1alpha1.user import (
    BINDINGS_SYNCED_CONDITION,
    BindingObservation,
    User,
    UserSpec,
    UserStatus,
)
from k8soperator.models.v1alpha1.userbinding import (
    SYNCED_CONDITION,
    UserBinding,
    UserBindingSpec,
    UserBindingStatus,
    is_synced,
)

__all__ = [
    "API_VERSION",
    "BINDINGS_SYNCED_CONDITION",
    "BindingObservation",
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
    "SYNCED_CONDITION",
    "User",
    "UserBinding",
    "UserBindingSpec",
    "UserBindingStatus",
    "UserSpec",
    "UserStatus",
    "is_synced",
]
