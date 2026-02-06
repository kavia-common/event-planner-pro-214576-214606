from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type (always 'bearer')")
    user: "UserPublic"


class UserPublic(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email (unique)")
    password: str = Field(..., min_length=4, description="User password")
    full_name: str = Field(..., min_length=1, description="Full name")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class EventBase(BaseModel):
    title: str = Field(..., min_length=1, description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    location: Optional[str] = Field(None, description="Event location")
    starts_at: datetime = Field(..., description="Event start datetime (ISO8601)")
    ends_at: Optional[datetime] = Field(None, description="Event end datetime (ISO8601)")
    capacity: Optional[int] = Field(None, ge=0, description="Maximum capacity (optional)")


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    location: Optional[str] = Field(None, description="Event location")
    starts_at: Optional[datetime] = Field(None, description="Event start datetime (ISO8601)")
    ends_at: Optional[datetime] = Field(None, description="Event end datetime (ISO8601)")
    capacity: Optional[int] = Field(None, ge=0, description="Maximum capacity (optional)")


class EventOut(EventBase):
    id: uuid.UUID
    creator_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    rsvp_counts: dict[str, int] = Field(default_factory=dict, description="Counts per RSVP status")

    class Config:
        from_attributes = True


RSVPStatus = Literal["going", "interested", "declined"]


class RSVPSetRequest(BaseModel):
    status: RSVPStatus = Field(..., description="RSVP status: going | interested | declined")


class RSVPOut(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    user_id: uuid.UUID
    status: RSVPStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


TokenResponse.model_rebuild()
