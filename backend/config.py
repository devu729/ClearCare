from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Google Gemini — free, no card needed
    gemini_api_key:       str

    # Supabase
    supabase_url:         str
    supabase_service_key: str

    # ChromaDB — local folder
    chroma_persist_path:  str = "./chroma_db"

    # CORS
    allowed_origins:      str = "http://localhost:3000"

    # Environment
    environment:          str = "development"

    # Gmail SMTP — for sending emails
    gmail_address:        str = ""
    gmail_app_password:   str = ""
    resend_api_key: str = ""

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()