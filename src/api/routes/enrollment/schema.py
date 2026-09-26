"""Enrollment request and response bodies."""

from typing import Self

from pydantic import Field

from cloudcoil.pydantic import BaseModel

from api.lib.common.jwt import Token
from k8soperator.models.v1alpha1.user import User


class CheckRequest(BaseModel):
    """Invite code to check."""

    code: str


class CheckResponse(BaseModel):
    """Whether the invite code can be redeemed."""

    valid: bool


class EnrollRequest(BaseModel):
    """Invite code to redeem and the callsign to take."""

    code: str
    callsign: str = Field(min_length=1)


class EnrollmentStatus(BaseModel):
    """Enrollment of the user, as shown to themselves."""

    callsign: str
    approval_code: str | None = Field(alias="approvalCode")
    approved: bool

    @classmethod
    def from_resource(cls, user: User) -> Self:
        """Enrollment status of the User resource."""
        return cls(
            callsign=user.spec.callsign,
            approval_code=user.spec.approval_code,
            approved=user.spec.approved_at is not None,
        )


class EnrollResponse(BaseModel):
    """Enrollment of the created user and their enrollment token."""

    status: EnrollmentStatus
    token: Token
