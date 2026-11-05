from pydantic import model_validator
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
    media_storage_driver: str = "s3"
    media_local_root: str = "./data/media"
    media_bucket: str | None = None
    media_region: str = "auto"
    media_endpoint_url: str | None = None
    media_access_key_id: str | None = None
    media_secret_access_key: str | None = None
    media_public_base_url: str | None = None
    upload_max_bytes: int = 1073741824
    redis_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_production_configuration(self):
        if self.app_env.lower() != "production":
            return self
        if len(self.secret_key) < 32 or self.secret_key.startswith("replace-with-"):
            raise ValueError("Production SECRET_KEY must be a unique random value with at least 32 characters.")
        if self.debug:
            raise ValueError("DEBUG must be false in production.")
        if not self.session_cookie_secure:
            raise ValueError("SESSION_COOKIE_SECURE must be true in production.")
        if "*" in self.cors_origin_list:
            raise ValueError("Wildcard CORS origins are not allowed in production.")
        if not self.cors_origin_list:
            raise ValueError("Production CORS_ORIGINS must contain the deployed site origin.")
        if not self.database_url.lower().startswith("mysql+pymysql://"):
            raise ValueError("Production DATABASE_URL must use the MySQL PyMySQL driver.")
        if self.media_storage_driver.lower() != "s3":
            raise ValueError("Production media storage must use the configured S3-compatible driver.")
        if not all((self.media_bucket, self.media_access_key_id, self.media_secret_access_key)):
            raise ValueError("Production media storage requires MEDIA_BUCKET, MEDIA_ACCESS_KEY_ID and MEDIA_SECRET_ACCESS_KEY.")
        return self

settings = Settings()
