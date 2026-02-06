from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.api.core.auth import get_current_user
from src.api.core.db import db_session
from src.api.models import Event, RSVP, User
from src.api.schemas import EventCreate, EventOut, EventUpdate

router = APIRouter(prefix="/events", tags=["events"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _event_to_out(db: Session, event: Event) -> EventOut:
    counts_rows = db.execute(
        select(RSVP.status, func.count(RSVP.id)).where(RSVP.event_id == event.id).group_by(RSVP.status)
    ).all()
    counts = {status: int(cnt) for status, cnt in counts_rows}
    return EventOut(
        id=event.id,
        creator_user_id=event.creator_user_id,
        title=event.title,
        description=event.description,
        location=event.location,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        capacity=event.capacity,
        created_at=event.created_at,
        updated_at=event.updated_at,
        rsvp_counts=counts,
    )


@router.get(
    "",
    response_model=list[EventOut],
    summary="List events",
    description="Returns a list of events ordered by start time.",
    operation_id="list_events",
)
def list_events(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[EventOut]:
    """List events (public)."""
    with db_session() as db:
        events = db.scalars(
            select(Event).order_by(Event.starts_at.asc()).limit(limit).offset(offset)
        ).all()
        return [_event_to_out(db, e) for e in events]


@router.get(
    "/{event_id}",
    response_model=EventOut,
    summary="Get event",
    description="Fetch a single event by id.",
    operation_id="get_event",
)
def get_event(event_id: uuid.UUID) -> EventOut:
    """Get event by ID (public)."""
    with db_session() as db:
        event = db.get(Event, event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        return _event_to_out(db, event)


@router.post(
    "",
    response_model=EventOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create event",
    description="Create a new event. Requires authentication.",
    operation_id="create_event",
)
def create_event(payload: EventCreate, current_user: User = Depends(get_current_user)) -> EventOut:
    """Create an event for the authenticated user."""
    with db_session() as db:
        now = _utcnow()
        event = Event(
            creator_user_id=current_user.id,
            title=payload.title,
            description=payload.description,
            location=payload.location,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
            capacity=payload.capacity,
            created_at=now,
            updated_at=now,
        )
        db.add(event)
        db.flush()
        return _event_to_out(db, event)


@router.put(
    "/{event_id}",
    response_model=EventOut,
    summary="Update event",
    description="Update an event. Only the creator can update. Requires authentication.",
    operation_id="update_event",
)
def update_event(
    event_id: uuid.UUID,
    payload: EventUpdate,
    current_user: User = Depends(get_current_user),
) -> EventOut:
    """Update an existing event."""
    with db_session() as db:
        event = db.get(Event, event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        if event.creator_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed")

        if payload.title is not None:
            event.title = payload.title
        if payload.description is not None:
            event.description = payload.description
        if payload.location is not None:
            event.location = payload.location
        if payload.starts_at is not None:
            event.starts_at = payload.starts_at
        if payload.ends_at is not None:
            event.ends_at = payload.ends_at
        if payload.capacity is not None:
            event.capacity = payload.capacity

        event.updated_at = _utcnow()
        db.add(event)
        db.flush()
        return _event_to_out(db, event)


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete event",
    description="Delete an event. Only the creator can delete. Requires authentication.",
    operation_id="delete_event",
)
def delete_event(event_id: uuid.UUID, current_user: User = Depends(get_current_user)) -> None:
    """Delete an event."""
    with db_session() as db:
        event = db.get(Event, event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        if event.creator_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed")
        db.delete(event)
        return None
