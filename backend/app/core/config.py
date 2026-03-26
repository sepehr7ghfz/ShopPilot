from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _load_env_files() -> None:
    """Load backend and workspace-level env files for local development."""
    backend_root = Path(__file__).resolve().parents[2]
    workspace_root = Path(__file__).resolve().parents[3]

    load_dotenv(backend_root / ".env", override=False)
    load_dotenv(workspace_root / ".env", override=False)


_load_env_files()


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    app_name: str = "ShopPilot API"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    api_prefix: str = "/api"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    use_llm_orchestrator: bool = True
    session_memory_turns: int = 8
    use_text_rag: bool = True
    rag_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("APP_NAME", cls.app_name),
            app_version=os.getenv("APP_VERSION", cls.app_version),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", cls.log_level).upper(),
            api_prefix=os.getenv("API_PREFIX", cls.api_prefix),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", cls.openai_model),
            use_llm_orchestrator=os.getenv("USE_LLM_ORCHESTRATOR", "true").lower() == "true",
            session_memory_turns=int(os.getenv("SESSION_MEMORY_TURNS", str(cls.session_memory_turns))),
            use_text_rag=os.getenv("USE_TEXT_RAG", "true").lower() == "true",
            rag_model_name=os.getenv("RAG_MODEL_NAME", cls.rag_model_name),
        )


settings = Settings.from_env()
