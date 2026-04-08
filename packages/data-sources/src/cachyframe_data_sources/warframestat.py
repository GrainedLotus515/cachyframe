from __future__ import annotations

from typing import Any

import httpx
from cachyframe_core.settings import get_settings

from .cache import FileCache


class WarframeStatClient:
    def __init__(
        self,
        base_url: str = "https://api.warframestat.us",
        *,
        timeout: float = 20.0,
    ) -> None:
        settings = get_settings()
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)
        self._cache = FileCache(settings.paths.cache_dir / "warframestat")

    async def _get(
        self,
        path: str,
        *,
        ttl_seconds: int = 300,
        params: dict[str, Any] | None = None,
    ) -> Any:
        cache_key = f"{path}:{params or {}}"
        cached = self._cache.get(cache_key, ttl_seconds=ttl_seconds)
        if cached is not None:
            return cached
        response = await self._client.get(path, params=params)
        response.raise_for_status()
        payload = response.json()
        self._cache.set(cache_key, payload)
        return payload

    async def get_worldstate(self, platform: str = "pc") -> dict[str, Any]:
        return await self._get(f"/{platform}", ttl_seconds=60)

    async def get_worldstate_slice(self, path: str, platform: str = "pc") -> Any:
        return await self._get(f"/{platform}/{path}", ttl_seconds=60)

    async def get_items(self, language: str = "en") -> list[dict[str, Any]]:
        return await self._get("/items", ttl_seconds=3600, params={"language": language})

    async def search_items(self, query: str, language: str = "en") -> list[dict[str, Any]]:
        return await self._get(
            f"/items/search/{query}",
            ttl_seconds=900,
            params={"language": language},
        )

    async def search_drops(self, query: str) -> list[dict[str, Any]]:
        return await self._get(f"/drops/search/{query}", ttl_seconds=900)

    async def get_rivens(self, platform: str = "pc", language: str = "en") -> dict[str, Any]:
        return await self._get(
            f"/{platform}/rivens",
            ttl_seconds=1800,
            params={"language": language},
        )

    async def get_catalog(self, path: str, language: str = "en") -> Any:
        return await self._get(f"/{path}", ttl_seconds=3600, params={"language": language})

    async def close(self) -> None:
        await self._client.aclose()
