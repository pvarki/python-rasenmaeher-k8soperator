"""User custom resource."""

from datetime import datetime
from typing import Annotated

from pydantic import Field

from cloudcoil.crd import ListType, PrinterColumn, custom_resource
from cloudcoil.pydantic import BaseModel
from cloudcoil.resources import Resource

from rmk8soperator.models.v1alpha1.common import API_VERSION, ObjectRef, PlatformStatus, ResolvedRef


class UserSpec(BaseModel):
    """Desired identity of a platform user."""

    callsign: Annotated[str, PrinterColumn(name="Callsign")] = Field(
        min_length=1,
        description="Unique callsign used to identify the user on the platform.",
    )
    revoked_at: Annotated[datetime | None, PrinterColumn(name="Revoked")] = Field(
        default=None,
        alias="revokedAt",
        description="RFC 3339 timestamp when the user was revoked; omit if the user is active.",
    )
    role_refs: Annotated[list[ObjectRef], ListType("map", keys=("name",))] = Field(
        default_factory=list,
        alias="roleRefs",
        description="References to roles assigned directly to the user.",
    )
    group_refs: Annotated[list[ObjectRef], ListType("map", keys=("name",))] = Field(
        default_factory=list,
        alias="groupRefs",
        description="References to groups the user belongs to.",
    )
    approval_code: str | None = Field(
        default=None,
        alias="approvalCode",
        description="Invite approval code used to authorize the user.",
    )
    approved_at: Annotated[datetime | None, PrinterColumn(name="Approved")] = Field(
        default=None,
        alias="approvedAt",
        description="RFC 3339 timestamp when the user was approved; omit while approval is pending.",
    )


class UserStatus(PlatformStatus):
    """Observed identity material and resolved role and group UIDs for a user."""

    public_key: str | None = Field(
        default=None,
        alias="publicKey",
        description="Public key signature of the user's mTLS certificate, observed from the cluster.",
    )
    roles: Annotated[list[ResolvedRef], ListType("map", keys=("name",))] = Field(
        default_factory=list,
        description="Names and UIDs of the roles assigned directly to the user.",
    )
    groups: Annotated[list[ResolvedRef], ListType("map", keys=("name",))] = Field(
        default_factory=list,
        description="Names and UIDs of the groups the user belongs to.",
    )


@custom_resource(
    api_version=API_VERSION,
    plural="users",
    scope="Cluster",
    short_names=("oduser",),
)
class User(Resource):
    """Cluster-scoped platform user."""

    spec: UserSpec = Field(description="Desired configuration of the user.")
    status: UserStatus | None = Field(
        default=None,
        description="Current observed state of the user.",
    )
