import pytest
from pydantic import ValidationError

from config.settings import Settings


def production_settings(**overrides):
    values = {
        "app_env": "production",
        "debug": False,
        "secret_key": "production-only-random-secret-key-32-chars-minimum",
        "database_url": "mysql+pymysql://pyyt:strong-db-password@mysql:3306/pyyt",
        "cors_origins": "https://pyyt.example.com",
        "session_cookie_secure": True,
        "media_storage_driver": "s3",
        "media_bucket": "pyyt-videos",
        "media_access_key_id": "access-key",
        "media_secret_access_key": "secret-key",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_valid_production_configuration_is_accepted():
    settings = production_settings()
    assert settings.app_env == "production"
    assert settings.cors_origin_list == ["https://pyyt.example.com"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"secret_key": "too-short"},
        {"debug": True},
        {"session_cookie_secure": False},
        {"cors_origins": "*"},
        {"database_url": "sqlite:///./pyyt.db"},
        {"media_bucket": None},
        {"media_access_key_id": None},
        {"media_secret_access_key": None},
        {"media_storage_driver": "local"},
    ],
)
def test_invalid_production_configuration_is_rejected(overrides):
    with pytest.raises(ValidationError):
        production_settings(**overrides)
