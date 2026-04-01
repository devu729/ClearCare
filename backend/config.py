from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Google Gemini
    gemini_api_key:       str

    # Supabase
    supabase_url:         str
    supabase_service_key: str

    # ChromaDB
    chroma_persist_path:  str = "./chroma_db"

    # CORS
    allowed_origins:      str = "http://localhost:3000"

    # Environment
    environment:          str = "development"

    # Email
    resend_api_key:       str = ""

    # ── Observability — Langfuse (free at cloud.langfuse.com) ─────
    # Sign up free at https://cloud.langfuse.com
    # Settings → API Keys → Create new keys
    langfuse_public_key:  str = ""
    langfuse_secret_key:  str = ""
    langfuse_host:        str = "https://cloud.langfuse.com"

    # ── Auth0 Token Vault ──────────────────────────────────────────
    auth0_domain:                   str = ""
    auth0_audience:                 str = ""
    auth0_client_id:                str = ""
    auth0_client_secret:            str = ""
    auth0_custom_api_client_id:     str = ""
    auth0_custom_api_client_secret: str = ""

    @property
    def origins_list(self) -> list[str]:
        origins = [o.strip() for o in self.allowed_origins.split(",")]
        if "http://localhost:3000" not in origins:
            origins.append("http://localhost:3000")
        return origins

    @property
    def observability_enabled(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)

    @property
    def token_vault_enabled(self) -> bool:
        return bool(self.auth0_domain and self.auth0_custom_api_client_id)

    model_config = {
        "env_file":          ".env",
        "env_file_encoding": "utf-8",
        "env_ignore_empty":  True,
        "extra":             "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    import logging
    logger = logging.getLogger(__name__)
    s = Settings()
    logger.info(f"Settings loaded — ENVIRONMENT: {s.environment}")
    logger.info(f"Observability enabled: {s.observability_enabled}")
    logger.info(f"Token Vault enabled: {s.token_vault_enabled}")
    return s