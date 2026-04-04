from __future__ import annotations

from typing import Dict, List, Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings and secrets.

    This central type is used throughout the codebase so that the
    behaviour of FastAPI and the agents can be driven by environment
    variables. pydantic-settings will automatically read from the
    environment (including an optional `.env` file in local development).

    ``ENV`` is the only flag that should be set to ``production`` when the
    service is running on the cloud; in that mode several conveniences such as
    OpenAPI docs are disabled and CORS origins are locked down.
    """

    # ---------------------------------------------------------------
    # runtime environment
    # ---------------------------------------------------------------
    ENV: Literal["local", "production", "test"] = "local"

    @property
    def is_production(self) -> bool:  # pragma: no cover - trivial
        return self.ENV.lower() == "production"

    # ---------------------------------------------------------------
    # external services and secrets
    # ---------------------------------------------------------------
    OPENAI_API_KEY: str

    REDIS_URL: str = "redis://localhost:6379"
    SESSION_TTL_SECONDS: int = 1_800  # default 30 minutes for Redis sessions

    FRONTEND_ORIGINS: List[str] = ["http://localhost:3000"]

    # ---------------------------------------------------------------
    # prompt versioning (existing behaviour)
    # ---------------------------------------------------------------
    PROMPT_VERSIONS: Dict[str, str] = {
        "input_guardrail": "v1.0",
        "orchestrator": "v1.0",
        "clinical_analysis": "v1.0",
        "risk_assessment": "v1.0",
        "qna": "v1.0",
        "compliance": "v1.0",
        "insights_summary": "v1.0",
    }

    # Default version if module not in PROMPT_VERSIONS
    DEFAULT_PROMPT_VERSION: str = "v1.0"

    class Config:  # configuration for pydantic-settings
        env_file = ".env"
        env_file_encoding = "utf-8"

    # Rate limit constants
    MAX_MESSAGES_PER_SESSION: int = 50  # max messages per session lifetime
    MAX_UPLOADS_PER_SESSION: int = 3  # max file uploads per session lifetime

    # Langfuse configuration
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_BASE_URL: str


settings = Settings()
