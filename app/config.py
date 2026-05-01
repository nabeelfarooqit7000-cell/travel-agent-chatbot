from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Travel Agent Chatbot API"
    app_env: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    cors_allow_origins: str = "*"

    sabre_base_url: str = "https://api.cert.platform.sabre.com"
    sabre_auth_url: str = "https://api.cert.platform.sabre.com/v2/auth/token"
    sabre_flight_shop_path: str = "/v4/offers/shop"
    sabre_client_id: str = ""
    sabre_client_secret: str = ""
    sabre_cpa_id: str = ""
    sabre_pcc: str = ""
    sabre_requestor_company_code: str = "TN"
    sabre_iso_country: str = "PK"
    sabre_timeout_seconds: float = 30.0
    admin_setup_key: str = ""
    knowledge_json_path: str = "app/data/knowledge_base.json"
    knowledge_backup_dir: str = "app/data/backups"
    admin_rate_limit_per_minute: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_cors_origins() -> list[str]:
    settings = get_settings()
    origins = [origin.strip() for origin in settings.cors_allow_origins.split(",") if origin.strip()]
    return origins or ["*"]
