"""Invite request and response bodies."""

from datetime import datetime
from typing import Self

from pydantic import Field

from cloudcoil.apimachinery import Time
from cloudcoil.pydantic import BaseModel

from api.lib.common.invites import used_count
from k8soperator.models.v1alpha1.common import ObjectRef
from k8soperator.models.v1alpha1.invite import Invite


class InviteResponse(BaseModel):
    """Invite, as shown to admins."""

    code: str
    role_refs: list[ObjectRef] = Field(alias="roleRefs")
    group_refs: list[ObjectRef] = Field(alias="groupRefs")
    use_count: int = Field(alias="useCount")
    used: int
    valid_until: datetime | None = Field(alias="validUntil")
    created_at: Time | None = Field(alias="createdAt")

    @classmethod
    def from_resource(cls, invite: Invite) -> Self:
        """Response for the Invite resource."""
        return cls(
            code=invite.spec.code,
            role_refs=invite.spec.role_refs,
            group_refs=invite.spec.group_refs,
            use_count=invite.spec.use_count,
            used=used_count(invite),
            valid_until=invite.spec.valid_until,
            created_at=invite.metadata.creation_timestamp if invite.metadata else None,
        )

    @classmethod
    def from_resources(cls, invites: list[Invite]) -> list[Self]:
        """Responses for the Invite resources."""
        return [cls.from_resource(invite) for invite in invites]
