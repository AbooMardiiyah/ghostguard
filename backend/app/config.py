"""GhostGuard configuration — loaded from environment variables."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_path: str = "data/db/ghostguard.db"

    # Identity provider
    identity_provider: str = "mock"  # "mock" or "dojah"
    dojah_app_id: str = ""
    dojah_secret_key: str = ""
    dojah_base_url: str = "https://sandbox.dojah.io"

    # LLM
    llm_provider: str = "mock"  # "together", "gemini", "openai", or "mock"
    together_api_key: str = ""
    together_model: str = "meta-llama/Llama-3.1-70B-Instruct-Turbo"
    gemini_api_key: str = ""
    openai_api_key: str = ""

    # PII masking
    pii_hmac_secret: str = "ghostguard-demo-secret-change-in-prod"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Odoo
    odoo_url: str = ""
    odoo_db: str = ""
    odoo_username: str = ""
    odoo_password: str = ""

    # Email / SMTP
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "ghostguard@sterlingdist.com"

    @property
    def db_path(self) -> Path:
        return Path(self.database_path)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
