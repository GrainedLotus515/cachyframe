from __future__ import annotations

from cachyframe_core.settings import get_settings

from .database import create_async_session_factory
from .repositories import StorageRepository


def create_repository(backend: bool = False) -> StorageRepository:
    settings = get_settings()
    database_url = settings.database.backend_url if backend else settings.database.local_url
    session_factory = create_async_session_factory(database_url)
    return StorageRepository(
        session_factory=session_factory,
        diagnostics_dir=settings.paths.diagnostics_dir,
    )
