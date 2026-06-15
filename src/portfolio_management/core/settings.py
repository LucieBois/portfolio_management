from pathlib import Path
from typing import ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PATH_REPO_ROOT = Path(__file__).parent.parent.parent.parent

PATH_BASE = PATH_REPO_ROOT / "src" / "portfolio_management"


class DatabaseSettings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=str(PATH_REPO_ROOT / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    DB_RELATIVE: str = Field(
        default=...,
        alias="DB_PATH",
        description="Relative path to the db, from repo root",
        exclude=True,
    )

    @property
    def DB_ABSOLUTE_PATH(self) -> Path:
        """Return absolute path to the SQLite DB"""
        return PATH_REPO_ROOT / self.DB_RELATIVE

    @property
    def DB_URI(self) -> str:
        """Return SQLite URI"""
        return f"sqlite:///{self.DB_ABSOLUTE_PATH}"
