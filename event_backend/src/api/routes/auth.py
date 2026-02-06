from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.api.core.auth import create_access_token, hash_password, verify_password
from src.api.core.db import db_session
from src.api.models import User
from src.api.schemas import LoginRequest, RegisterRequest, TokenResponse, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a user account and returns an access token.",
    operation_id="register_user",
)
def register_user(payload: RegisterRequest) -> TokenResponse:
    """Create a new user and return JWT access token."""
    with db_session() as db:
        user = User(
            email=str(payload.email).lower(),
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
        )
        db.add(user)
        try:
            db.flush()  # obtain user.id
        except IntegrityError as exc:
            raise HTTPException(status_code=400, detail="Email already registered") from exc

        token = create_access_token(user_id=user.id, email=user.email)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserPublic(id=user.id, email=user.email, full_name=user.full_name),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Validates credentials and returns an access token.",
    operation_id="login_user",
)
def login_user(payload: LoginRequest) -> TokenResponse:
    """Login using email/password and return JWT access token."""
    with db_session() as db:
        user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token(user_id=user.id, email=user.email)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserPublic(id=user.id, email=user.email, full_name=user.full_name),
        )
