from __future__ import annotations

from typing import Any

import httpx
from cachyframe_core.settings import get_settings

from .cache import FileCache


class WarframeMarketClient:
    def __init__(
        self,
        base_url: str = "https://api.warframe.market/v1",
        *,
        timeout: float = 20.0,
    ) -> None:
        settings = get_settings()
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers={"accept": "application/json", "platform": "pc"},
        )
        self._cache = FileCache(settings.paths.cache_dir / "warframe-market")

    async def get_orders_for_item(self, item_slug: str) -> dict[str, Any]:
        cache_key = f"orders:{item_slug}"
        cached = self._cache.get(cache_key, ttl_seconds=60)
        if cached is not None:
            return cached
        response = await self._client.get(f"/items/{item_slug}/orders")
        response.raise_for_status()
        payload = response.json()
        self._cache.set(cache_key, payload)
        return payload

    async def get_item_statistics(self, item_slug: str) -> dict[str, Any]:
        cache_key = f"statistics:{item_slug}"
        cached = self._cache.get(cache_key, ttl_seconds=300)
        if cached is not None:
            return cached
        response = await self._client.get(f"/items/{item_slug}/statistics")
        response.raise_for_status()
        payload = response.json()
        self._cache.set(cache_key, payload)
        return payload

    async def get_user_orders(self, username: str) -> dict[str, Any]:
        response = await self._client.get(f"/profile/{username}/orders")
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()
