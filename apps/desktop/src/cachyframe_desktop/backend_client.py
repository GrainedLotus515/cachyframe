from __future__ import annotations

from typing import Any

import httpx


class DesktopBackendClient:
    def __init__(self, base_url: str, *, timeout: float = 10.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def get_health(self) -> dict[str, Any]:
        response = await self._client.get("/healthz")
        response.raise_for_status()
        return response.json()

    async def get_worldstate(self) -> dict[str, Any]:
        response = await self._client.get("/api/client/v1/worldstate")
        response.raise_for_status()
        return response.json()

    async def get_dashboard(self, user_hash: str) -> dict[str, Any]:
        response = await self._client.get(
            "/api/client/v1/dashboard",
            params={"user_hash": user_hash},
        )
        response.raise_for_status()
        return response.json()

    async def get_foundry(self, user_hash: str) -> dict[str, Any]:
        response = await self._client.get("/api/client/v1/foundry", params={"user_hash": user_hash})
        response.raise_for_status()
        return response.json()

    async def get_inventory(self, user_hash: str, *, tradable_only: bool = False) -> dict[str, Any]:
        response = await self._client.get(
            "/api/client/v1/inventory",
            params={"user_hash": user_hash, "tradable_only": tradable_only},
        )
        response.raise_for_status()
        return response.json()

    async def get_relics(self, user_hash: str) -> dict[str, Any]:
        response = await self._client.get("/api/client/v1/relics", params={"user_hash": user_hash})
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()
