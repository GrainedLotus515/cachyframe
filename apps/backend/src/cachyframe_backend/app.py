from __future__ import annotations

from contextlib import asynccontextmanager

from cachyframe_core.compat import encode_relic_inventory
from cachyframe_core.derived import WorldstateSummary
from cachyframe_core.settings import get_settings
from cachyframe_data_sources import WarframeStatClient
from cachyframe_storage.bootstrap import create_repository
from cachyframe_storage.repositories import StorageRepository
from fastapi import FastAPI, HTTPException, Response

from .schemas import (
    AnalyticsOverviewResponse,
    CaptureEventBatchRequest,
    CaptureEventBatchResponse,
    DashboardResponse,
    DiagnosticsUploadRequest,
    FoundryResponse,
    InventoryResponse,
    PublicLinkCreateRequest,
    PublicLinkListResponse,
    RelicResponse,
    SnapshotRequest,
    SniperSubscriptionRequest,
    StatsBatchRequest,
    TradeBatchRequest,
)
from .services import BackendService


@asynccontextmanager
async def lifespan(app: FastAPI):
    repository = create_repository(backend=True)
    await repository.initialize()
    warframestat = WarframeStatClient()
    service = BackendService(repository, warframestat, platform=get_settings().platform)
    app.state.repository = repository
    app.state.service = service
    yield
    await warframestat.close()


def get_repository(app: FastAPI) -> StorageRepository:
    return app.state.repository


def get_service(app: FastAPI) -> BackendService:
    return app.state.service


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="CachyFrame Backend", version="0.1.0", lifespan=lifespan)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    @app.get("/api/client/v1/worldstate", response_model=WorldstateSummary)
    async def get_worldstate():
        service = get_service(app)
        return await service.worldstate_summary()

    @app.get("/api/stats/{user_hash}")
    async def get_stats(user_hash: str, secretToken: str | None = None):  # noqa: N803
        repository = get_repository(app)
        payload = await repository.get_player_stats_data(user_hash, secret_token=secretToken)
        if payload is None:
            raise HTTPException(status_code=404, detail="stats not found")
        return payload

    @app.get("/api/stats/public")
    async def get_public_stats(token: str):
        repository = get_repository(app)
        payload = await repository.get_public_stats(token)
        if payload is None:
            raise HTTPException(status_code=404, detail="public link not found")
        return payload

    @app.get("/api/stats/public/getRelicInventory")
    async def get_public_relic_inventory(publicToken: str):  # noqa: N803
        repository = get_repository(app)
        payload = await repository.get_public_stats(publicToken)
        if payload is None:
            raise HTTPException(status_code=404, detail="public link not found")
        snapshot = await repository.get_current_snapshot(payload.user_hash or settings.user_hash)
        if snapshot is None:
            raise HTTPException(status_code=404, detail="snapshot not found")
        return Response(
            content=encode_relic_inventory(snapshot.relics),
            media_type="application/octet-stream",
        )

    @app.post("/api/client/v1/stats/points:batch")
    async def post_stats_points(request: StatsBatchRequest):
        repository = get_repository(app)
        count = await repository.add_stats_points(request.user_hash, request.points)
        return {"accepted": count}

    @app.post("/api/client/v1/stats/trades:batch")
    async def post_trade_records(request: TradeBatchRequest):
        repository = get_repository(app)
        count = await repository.add_trades(request.user_hash, request.trades)
        return {"accepted": count}

    @app.post("/api/client/v1/account/snapshots")
    async def post_snapshot(request: SnapshotRequest):
        repository = get_repository(app)
        snapshot = await repository.upsert_snapshot(request.snapshot)
        return snapshot

    @app.post("/api/client/v1/capture-events:batch", response_model=CaptureEventBatchResponse)
    async def post_capture_events(request: CaptureEventBatchRequest):
        service = get_service(app)
        try:
            snapshot, accepted_trades = await service.ingest_capture_events(
                request.user_hash,
                request.events,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return CaptureEventBatchResponse(
            accepted_events=len(request.events),
            accepted_trades=accepted_trades,
            current_snapshot=snapshot,
        )

    @app.get("/api/client/v1/account/current")
    async def get_current_snapshot(user_hash: str):
        repository = get_repository(app)
        snapshot = await repository.get_current_snapshot(user_hash)
        if snapshot is None:
            raise HTTPException(status_code=404, detail="snapshot not found")
        return snapshot

    @app.get("/api/client/v1/capture-events")
    async def list_capture_events(user_hash: str, limit: int = 50):
        repository = get_repository(app)
        return await repository.list_capture_events(user_hash, limit=limit)

    @app.get("/api/client/v1/dashboard", response_model=DashboardResponse)
    async def get_dashboard(user_hash: str):
        service = get_service(app)
        return await service.dashboard(user_hash)

    @app.get("/api/client/v1/foundry", response_model=FoundryResponse)
    async def get_foundry(user_hash: str):
        service = get_service(app)
        summary = await service.foundry_summary(user_hash)
        if summary is None:
            raise HTTPException(status_code=404, detail="snapshot not found")
        return summary

    @app.get("/api/client/v1/inventory", response_model=InventoryResponse)
    async def get_inventory(user_hash: str, tradable_only: bool = False):
        service = get_service(app)
        summary = await service.inventory_summary(
            user_hash,
            tradable_only=tradable_only,
        )
        if summary is None:
            raise HTTPException(status_code=404, detail="snapshot not found")
        return summary

    @app.get("/api/client/v1/relics", response_model=RelicResponse)
    async def get_relics(user_hash: str):
        service = get_service(app)
        summary = await service.relic_summary(user_hash)
        if summary is None:
            raise HTTPException(status_code=404, detail="snapshot not found")
        return summary

    @app.post("/api/client/v1/public-links")
    async def create_public_link(request: PublicLinkCreateRequest):
        repository = get_repository(app)
        return await repository.create_public_link(
            request.user_hash,
            request.parts,
            username_when_public=request.username_when_public,
            ttl_days=request.ttl_days,
        )

    @app.get("/api/client/v1/public-links", response_model=PublicLinkListResponse)
    async def list_public_links(user_hash: str):
        repository = get_repository(app)
        return PublicLinkListResponse(items=await repository.list_public_links(user_hash))

    @app.delete("/api/client/v1/public-links/{link_id}")
    async def delete_public_link(link_id: str, user_hash: str):
        repository = get_repository(app)
        deleted = await repository.revoke_public_link(user_hash, link_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="link not found")
        return {"deleted": True}

    @app.get("/api/client/v1/analytics/overview", response_model=AnalyticsOverviewResponse)
    async def get_analytics_overview(user_hash: str):
        repository = get_repository(app)
        overview = await repository.analytics_overview(user_hash)
        return AnalyticsOverviewResponse.model_validate(overview)

    @app.get("/api/client/v1/analytics/items/{item_id}")
    async def get_item_analytics(item_id: str, user_hash: str):
        repository = get_repository(app)
        return await repository.analytics_for_item(user_hash, item_id)

    @app.post("/api/client/v1/sniper/subscriptions")
    async def create_sniper_subscription(request: SniperSubscriptionRequest):
        repository = get_repository(app)
        return await repository.create_sniper_subscription(request.user_hash, request.subscription)

    @app.get("/api/client/v1/sniper/subscriptions")
    async def list_sniper_subscriptions(user_hash: str):
        repository = get_repository(app)
        return await repository.list_sniper_subscriptions(user_hash)

    @app.delete("/api/client/v1/sniper/subscriptions/{subscription_id}")
    async def delete_sniper_subscription(subscription_id: str, user_hash: str):
        repository = get_repository(app)
        deleted = await repository.delete_sniper_subscription(user_hash, subscription_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="subscription not found")
        return {"deleted": True}

    @app.post("/api/client/v1/diagnostics/upload")
    async def upload_diagnostics(request: DiagnosticsUploadRequest):
        repository = get_repository(app)
        upload_id = await repository.save_diagnostics(
            request.user_hash,
            request.filename,
            request.content_type,
            request.decode(),
        )
        return {"upload_id": upload_id}

    return app
