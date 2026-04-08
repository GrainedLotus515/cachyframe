from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_data_dir() -> Path:
    return Path.home() / ".local" / "share" / "cachyframe"


def _default_config_dir() -> Path:
    return Path.home() / ".config" / "cachyframe"


def _default_cache_dir() -> Path:
    return Path.home() / ".cache" / "cachyframe"


class RuntimePaths(BaseModel):
    config_dir: Path = Field(default_factory=_default_config_dir)
    data_dir: Path = Field(default_factory=_default_data_dir)
    cache_dir: Path = Field(default_factory=_default_cache_dir)
    logs_dir: Path = Field(default_factory=lambda: _default_data_dir() / "logs")
    diagnostics_dir: Path = Field(default_factory=lambda: _default_data_dir() / "diagnostics")
    ca_dir: Path = Field(default_factory=lambda: _default_data_dir() / "ca")


class DatabaseSettings(BaseModel):
    local_url: str = "sqlite+aiosqlite:///./cachyframe.db"
    backend_url: str = "sqlite+aiosqlite:///./cachyframe-backend.db"


class BackendSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8010
    cors_origins: list[str] = ["http://127.0.0.1", "http://localhost"]


class ProxySettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8899
    admin_port: int = 8900
    retain_raw_hours: int = 24
    mitm_mode: str = "regular"


class DesktopSettings(BaseModel):
    backend_url: str = "http://127.0.0.1:8010"
    x11_only_overlays: bool = True
    refresh_worldstate_seconds: int = 300


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CACHYFRAME_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    environment: str = "development"
    user_hash: str = "local-user"
    secret_token: str = "dev-secret"
    platform: str = "pc"
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    backend: BackendSettings = Field(default_factory=BackendSettings)
    proxy: ProxySettings = Field(default_factory=ProxySettings)
    desktop: DesktopSettings = Field(default_factory=DesktopSettings)
    paths: RuntimePaths = Field(default_factory=RuntimePaths)


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    settings = AppSettings()
    for path in (
        settings.paths.config_dir,
        settings.paths.data_dir,
        settings.paths.cache_dir,
        settings.paths.logs_dir,
        settings.paths.diagnostics_dir,
        settings.paths.ca_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)
    return settings
