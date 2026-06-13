"""Tests for database configuration loading and validation."""

import pytest
from pydantic import ValidationError

from mcd_ua_idw.config import Settings


DATABASE_URL = "postgresql+psycopg://app:app@localhost:5432/app"


def test_settings_load_database_url_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", DATABASE_URL)

    settings = Settings(_env_file=None)

    assert settings.database_url == DATABASE_URL


def test_settings_load_database_url_from_dotenv(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(f"DATABASE_URL={DATABASE_URL}\n", encoding="utf-8")

    settings = Settings(_env_file=env_file)

    assert settings.database_url == DATABASE_URL


def test_settings_require_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError, match="DATABASE_URL"):
        Settings(_env_file=None)


@pytest.mark.parametrize(
    ("database_url", "error_message"),
    [
        ("postgresql://app:app@localhost/app", r"postgresql\+psycopg"),
        ("sqlite+aiosqlite:///local.db", r"postgresql\+psycopg"),
        ("not-a-url", "valid SQLAlchemy URL"),
    ],
)
def test_settings_require_async_psycopg_driver(
    database_url: str, error_message: str
) -> None:
    with pytest.raises(ValidationError, match=error_message):
        Settings(DATABASE_URL=database_url, _env_file=None)
