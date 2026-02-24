from pydantic_settings import BaseSettings
from typing import Dict


class Settings(BaseSettings):
    """Application settings with per-module prompt versioning for LLMOps."""
    
    # Per-module prompt versioning for independent agent control
    # Each agent/module can have its own version
    PROMPT_VERSIONS: Dict[str, str] = {
        "orchestrator": "v1.0",
        "clinical_analysis": "v1.0",
        "risk_assessment": "v1.0",
        "qna": "v1.0",
        "compliance": "v1.0",
        "insight_summary": "v1.0"
    }
    
    # Default version if module not in PROMPT_VERSIONS
    DEFAULT_PROMPT_VERSION: str = "v1.0"
    
settings = Settings()
