from __future__ import annotations

import lzma

import httpx
from cachyframe_core.settings import get_settings

from .cache import FileCache


class OfficialWarframeClient:
    INDEX_URL = "https://origin.warframe.com/PublicExport/index_en.txt.lzma"
    DROP_TABLES_URL = "https://www.warframe.com/droptables"

    def __init__(self, *, timeout: float = 20.0) -> None:
        settings = get_settings()
        self._client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)
        self._cache = FileCache(settings.paths.cache_dir / "official-warframe")

    async def fetch_export_index(self) -> list[str]:
        cached = self._cache.get("index", ttl_seconds=3600)
        if cached is not None:
            return cached
        response = await self._client.get(self.INDEX_URL)
        response.raise_for_status()
        decompressed = lzma.decompress(response.content, format=lzma.FORMAT_ALONE).decode("utf-8")
        lines = [line for line in decompressed.splitlines() if line.strip()]
        self._cache.set("index", lines)
        return lines

    async def fetch_drop_tables_html(self) -> str:
        cached = self._cache.get("droptables-html", ttl_seconds=3600)
        if cached is not None:
            return str(cached)
        response = await self._client.get(self.DROP_TABLES_URL)
        response.raise_for_status()
        payload = response.text
        self._cache.set("droptables-html", payload)
        return payload

    async def close(self) -> None:
        await self._client.aclose()

