from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.api.core.auth import get_current_user
from src.api.core.db import db_session
from src.api.models import Event, RSVP, User
from src.api.schemas import RSVPOut, RSVPSetRequest

router = APIRouter(prefix="/events/{event_id}/rsvps", tags=["rsvps"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@router.get(
    "",
    response_model=list[RSVPOut],
    summary="List RSVPs for an event",
    description="Returns RSVPs for the given event. Public.",
    operation_id="list_event_rsvps",
)
def list_event_rsvps(event_id: uuid.UUID) -> list[RSVPOut]:
    """List RSVPs for an event."""
    with db_session() as db:
        event = db.get(Event, event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        rsvps = db.scalars(select(RSVP).where(RSVP.event_id == event_id).order_by(RSVP.created_at.asc())).all()
        return [RSVPOut.model_validate(r) for r in rsvps]


@router.put(
    "/me",
    response_model=RSVPOut,
    summary="Set my RSVP",
    description="Create or update the authenticated user's RSVP for this event.",
    operation_id="set_my_rsvp",
)
def set_my_rsvp(
    event_id: uuid.UUID,
    payload: RSVPSetRequest,
    current_user: User = Depends(get_current_user),
) -> RSVPOut:
    """Create or update current user's RSVP for the event."""
    with db_session() as db:
        event = db.get(Event, event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")

        existing = db.scalar(select(RSVP).where(RSVP.event_id == event_id, RSVP.user_id == current_user.id))
        now = _utcnow()

        if existing:
            existing.status = payload.status
            existing.updated_at = now
            db.add(existing)
            db.flush()
            return RSVPOut.model_validate(existing)

        rsvp = RSVP(
            event_id=event_id,
            user_id=current_user.id,
            status=payload.status,
            created_at=now,
            updated_at=now,
        )
        db.add(rsvp)
        try:
            db.flush()
        except IntegrityError as exc:
            # Handles the rare race where another request inserted same (event_id,user_id)
            raise HTTPException(status_code=409, detail="RSVP already exists") from exc
        return RSVPOut.model_validate(rsvp)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove my RSVP",
    description="Deletes the authenticated user's RSVP for this event (if any).",
    operation_id="delete_my_rsvp",
)
def delete_my_rsvp(event_id: uuid.UUID, current_user: User = Depends(get_current_user)) -> None:
    """Delete current user's RSVP for the event."""
    with db_session() as db:
        rsvp = db.scalar(select(RSVP).where(RSVP.event_id == event_id, RSVP.user_id == current_user.id))
        if rsvp is None:
            return None
        db.delete(rsvp)
        return None
