from __future__ import annotations

from cachyframe_collectors.reconciliation import AccountSnapshotReconciler
from cachyframe_core.derived import (
    DashboardSummary,
    FoundrySummary,
    InventorySummary,
    RelicSummary,
    SnapshotSummary,
    WorldstateSummary,
    build_foundry_summary,
    build_inventory_summary,
    build_relic_summary,
    build_snapshot_summary,
    build_worldstate_summary,
)
from cachyframe_core.models import (
    AccountProgressEvent,
    AccountSnapshot,
    CaptureEvent,
    InventoryDeltaEvent,
    InventorySnapshotEvent,
    MarketRelevantItemEvent,
    RelicInventoryEvent,
    SessionBoundaryEvent,
    TradeHandshakeEvent,
)
from cachyframe_data_sources import WarframeStatClient
from cachyframe_storage.repositories import StorageRepository


class BackendService:
    def __init__(
        self,
        repository: StorageRepository,
        warframestat: WarframeStatClient,
        *,
        platform: str,
    ) -> None:
        self._repository = repository
        self._warframestat = warframestat
        self._platform = platform

    async def ingest_capture_events(
        self,
        user_hash: str,
        events: list[CaptureEvent],
    ) -> tuple[AccountSnapshot | None, int]:
        current_snapshot = await self._repository.get_current_snapshot(user_hash)
        reconciler = AccountSnapshotReconciler(
            current_snapshot
            or AccountSnapshot(user_hash=user_hash, source="capture_ingest")
        )
        accepted_trades = 0
        snapshot_changed = False

        await self._repository.add_capture_events(user_hash, events)

        for event in sorted(events, key=lambda item: item.occurred_at):
            if isinstance(event, InventorySnapshotEvent):
                if event.snapshot.user_hash != user_hash:
                    raise ValueError("snapshot user_hash does not match batch user_hash")
                snapshot_changed = True
                reconciler.apply_event(event)
            elif isinstance(
                event,
                InventoryDeltaEvent
                | RelicInventoryEvent
                | AccountProgressEvent
                | MarketRelevantItemEvent,
            ):
                snapshot_changed = True
                reconciler.apply_event(event)
            elif isinstance(event, TradeHandshakeEvent):
                accepted_trades += 1
                await self._repository.add_trades(user_hash, [event.trade])
                reconciler.snapshot.metadata["last_trade_user"] = event.trade.user
                reconciler.snapshot.captured_at = event.occurred_at
            elif isinstance(event, SessionBoundaryEvent):
                snapshot_changed = True
                reconciler.snapshot.metadata["last_session_phase"] = event.phase
                reconciler.snapshot.metadata["last_session_metadata"] = event.metadata
                reconciler.snapshot.captured_at = event.occurred_at

        current = reconciler.snapshot if snapshot_changed or current_snapshot else None
        if current is not None:
            current.user_hash = user_hash
            if current_snapshot is not None:
                current.secret_token = current.secret_token or current_snapshot.secret_token
                current.username = current.username or current_snapshot.username
            await self._repository.upsert_snapshot(current)
        return current, accepted_trades

    async def worldstate_summary(self) -> WorldstateSummary:
        payload = await self._warframestat.get_worldstate(self._platform)
        return build_worldstate_summary(payload)

    async def snapshot_summary(self, user_hash: str) -> SnapshotSummary | None:
        snapshot = await self._repository.get_current_snapshot(user_hash)
        if snapshot is None:
            return None
        return build_snapshot_summary(snapshot)

    async def foundry_summary(self, user_hash: str) -> FoundrySummary | None:
        snapshot = await self._repository.get_current_snapshot(user_hash)
        if snapshot is None:
            return None
        return build_foundry_summary(snapshot)

    async def inventory_summary(
        self,
        user_hash: str,
        *,
        tradable_only: bool = False,
    ) -> InventorySummary | None:
        snapshot = await self._repository.get_current_snapshot(user_hash)
        if snapshot is None:
            return None
        return build_inventory_summary(snapshot, tradable_only=tradable_only)

    async def relic_summary(self, user_hash: str) -> RelicSummary | None:
        snapshot = await self._repository.get_current_snapshot(user_hash)
        if snapshot is None:
            return None
        return build_relic_summary(snapshot)

    async def dashboard(self, user_hash: str) -> DashboardSummary:
        analytics = await self._repository.analytics_overview(user_hash)
        snapshot = await self.snapshot_summary(user_hash)
        try:
            worldstate = await self.worldstate_summary()
        except Exception:  # pragma: no cover - depends on network
            worldstate = None
        return DashboardSummary(
            worldstate=worldstate,
            snapshot=snapshot,
            analytics=analytics,
        )
