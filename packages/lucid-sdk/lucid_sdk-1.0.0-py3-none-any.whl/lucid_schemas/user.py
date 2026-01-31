"""User management schemas shared between verifier and observer."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

from .enums import UserRole


class OrganizationMember(BaseModel):
    """Organization member with role information."""
    id: UUID
    email: str
    role: UserRole
    is_active: bool
    joined_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class InviteUserRequest(BaseModel):
    """Request to invite a user to an organization."""
    email: EmailStr
    role: UserRole = UserRole.VIEWER


class InvitationResponse(BaseModel):
    """Response for invitation."""
    id: UUID
    email: str
    role: UserRole
    invited_by_email: str
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UpdateMemberRoleRequest(BaseModel):
    """Request to update a member's role."""
    role: UserRole
