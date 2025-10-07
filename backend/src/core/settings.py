"""Application settings management using pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Centralised configuration sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(..., alias="DATABASE_URL")
    casbin_db_url: str = Field(..., alias="CASBIN_DB_URL")
    kc_url: str = Field(..., alias="KC_URL")
    kc_realm: str = Field(..., alias="KC_REALM")
    kc_audience: str = Field(..., alias="KC_AUDIENCE")
    kc_client_id: str = Field(..., alias="KC_CLIENT_ID")
    jwt_leeway_seconds: int = Field(30, alias="JWT_LEEWAY_SECONDS")
    service_name: str = Field("keur-doctor-backend", alias="SERVICE_NAME")
    allow_origins: list[str] = Field(default_factory=lambda: ["*"], alias="ALLOW_ORIGINS")
    rate_limit_queries_per_min: int = Field(30, alias="RATE_LIMIT_QUERIES_PER_MIN")
    otel_exporter_otlp_endpoint: str | None = Field(
        default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    structlog_json: bool = Field(True, alias="STRUCTLOG_JSON")
    host: str = Field("0.0.0.0", alias="HOST")
    port: int = Field(8000, alias="PORT")
    casbin_model_path: str = Field("casbin/model.conf", alias="CASBIN_MODEL_PATH")
    casbin_policy_path: str = Field("casbin/seed_policy.csv", alias="CASBIN_POLICY_PATH")
    metrics_namespace: str = Field("keur_doctor", alias="METRICS_NAMESPACE")

    @field_validator("allow_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: Any) -> list[str]:
        if value in (None, "", "*"):
            return ["*"]
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return value
        raise ValueError("ALLOW_ORIGINS must be a comma-separated string or list")

    @property
    def kc_issuer(self) -> str:
        return f"{self.kc_url.rstrip('/')}/realms/{self.kc_realm}"

    @property
    def kc_jwks_url(self) -> str:
        return f"{self.kc_issuer}/protocol/openid-connect/certs"

    @property
    def kc_token_url(self) -> str:
        return f"{self.kc_issuer}/protocol/openid-connect/token"

    @property
    def sync_casbin_db_url(self) -> str:
        """Return a synchronous connection string for Casbin adapter."""
        if "+asyncpg" in self.casbin_db_url:
            return self.casbin_db_url.replace("+asyncpg", "+psycopg")
        return self.casbin_db_url

    def resolve_path(self, relative_path: str) -> Path:
        """Resolve a path relative to the project base directory."""
        candidate = Path(relative_path)
        if candidate.is_absolute():
            return candidate
        return (BASE_DIR / candidate).resolve()


@lru_cache(1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()

