from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./intentbid.db"
    secret_key: str = "dev-secret"
    env: str = "dev"
    max_offers_per_vendor_rfo: int = 5
    offer_cooldown_seconds: int = 0
    admin_api_key: str | None = None
    require_verified_vendors_for_hardware: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
