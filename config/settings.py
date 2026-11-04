from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Py-Yt"
    app_env: str = "development"
    debug: bool = False
    secret_key: str
    database_url: str
    cors_origins: str = "http://localhost:8000"
    session_cookie_secure: bool = True
    session_cookie_samesite: str = "lax"
    youtube_api_key: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None
    media_storage_driver: str = "local"
    media_local_root: str = "./data/media"
    redis_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

settings = Settings()
