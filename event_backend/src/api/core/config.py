import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    postgres_url: str
    jwt_secret: str
    jwt_algorithm: str
    jwt_exp_minutes: int
    cors_allow_origins: list[str]


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid integer for env var {name}: {value}") from exc


def _get_list_env(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    # Comma-separated
    return [v.strip() for v in value.split(",") if v.strip()]


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Load and validate runtime settings from environment variables.

    Expected env vars:
    - POSTGRES_URL: SQLAlchemy-compatible URL, e.g. postgresql+psycopg://user:pass@host:port/db
      (If only a raw postgres URL is provided, we will adapt it in db.py.)
    - JWT_SECRET: secret used to sign JWTs
    - JWT_ALGORITHM: (optional) defaults to HS256
    - JWT_EXPIRES_MINUTES: (optional) defaults to 60*24 (1 day)
    - CORS_ALLOW_ORIGINS: (optional) comma-separated list, defaults to http://localhost:3000
    """
    cors_default = ["http://localhost:3000"]

    return Settings(
        postgres_url=os.getenv("POSTGRES_URL", "").strip(),
        jwt_secret=os.getenv("JWT_SECRET", "").strip(),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256").strip(),
        jwt_exp_minutes=_get_int_env("JWT_EXPIRES_MINUTES", 60 * 24),
        cors_allow_origins=_get_list_env("CORS_ALLOW_ORIGINS", cors_default),
    )
