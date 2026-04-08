from __future__ import annotations

from cachyframe_data_sources import OfficialWarframeClient, WarframeMarketClient, WarframeStatClient
from cachyframe_storage.bootstrap import create_repository


class WorkerJobs:
    def __init__(self) -> None:
        self.repository = create_repository(backend=True)
        self.warframestat = WarframeStatClient()
        self.official = OfficialWarframeClient()
        self.market = WarframeMarketClient()

    async def startup(self) -> None:
        await self.repository.initialize()

    async def refresh_worldstate(self) -> dict:
        return await self.warframestat.get_worldstate()

    async def refresh_riven_stats(self) -> dict:
        return await self.warframestat.get_rivens()

    async def refresh_public_exports(self) -> list[str]:
        return await self.official.fetch_export_index()

    async def materialize_analytics(self, user_hash: str) -> dict[str, int | float]:
        return await self.repository.analytics_overview(user_hash)

