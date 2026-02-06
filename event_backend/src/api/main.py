from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.api.core.config import get_settings
from src.api.core.db import db_session
from src.api.routes.auth import router as auth_router
from src.api.routes.events import router as events_router
from src.api.routes.rsvps import router as rsvps_router

openapi_tags = [
    {"name": "health", "description": "Service health and diagnostics."},
    {"name": "auth", "description": "User registration and login (JWT)."},
    {"name": "events", "description": "Events CRUD."},
    {"name": "rsvps", "description": "RSVP management per event."},
]

app = FastAPI(
    title="Event Planner Pro API",
    description=(
        "Backend API for Event Planner Pro (FastAPI + PostgreSQL).\n\n"
        "Auth uses JWT Bearer tokens. Provide `Authorization: Bearer <token>` for protected routes."
    ),
    version="1.0.0",
    openapi_tags=openapi_tags,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(events_router)
app.include_router(rsvps_router)


@app.get(
    "/",
    tags=["health"],
    summary="Health check",
    description="Basic service health check.",
    operation_id="health_check",
)
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}


@app.get(
    "/health/db",
    tags=["health"],
    summary="Database health check",
    description="Checks that the API can connect to Postgres and run a simple query.",
    operation_id="db_health_check",
)
def db_health_check():
    """Database health check endpoint."""
    with db_session() as db:
        db.execute(text("SELECT 1"))
    return {"db": "ok"}
