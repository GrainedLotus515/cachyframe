from __future__ import annotations

import base64

from cachyframe_core.derived import DashboardSummary, FoundrySummary, InventorySummary, RelicSummary
from cachyframe_core.models import (
    AccountSnapshot,
    CaptureEvent,
    PublicLink,
    SniperSubscription,
    StatsPoint,
    TradeRecord,
)
from pydantic import BaseModel, Field


class StatsBatchRequest(BaseModel):
    user_hash: str
    points: list[StatsPoint] = Field(default_factory=list)


class TradeBatchRequest(BaseModel):
    user_hash: str
    trades: list[TradeRecord] = Field(default_factory=list)


class SnapshotRequest(BaseModel):
    snapshot: AccountSnapshot


class CaptureEventBatchRequest(BaseModel):
    user_hash: str
    events: list[CaptureEvent] = Field(default_factory=list)


class CaptureEventBatchResponse(BaseModel):
    accepted_events: int
    accepted_trades: int
    current_snapshot: AccountSnapshot | None = None


class PublicLinkCreateRequest(BaseModel):
    user_hash: str
    parts: int
    username_when_public: str | None = None
    ttl_days: int = 365


class PublicLinkListResponse(BaseModel):
    items: list[PublicLink]


class AnalyticsOverviewResponse(BaseModel):
    trade_count: int
    stats_point_count: int
    total_items: int
    total_relics: int


class DashboardResponse(DashboardSummary):
    pass


class FoundryResponse(FoundrySummary):
    pass


class InventoryResponse(InventorySummary):
    pass


class RelicResponse(RelicSummary):
    pass


class DiagnosticsUploadRequest(BaseModel):
    user_hash: str
    filename: str
    content_type: str = "application/octet-stream"
    content_base64: str

    def decode(self) -> bytes:
        return base64.b64decode(self.content_base64)


class SniperSubscriptionRequest(BaseModel):
    user_hash: str
    subscription: SniperSubscription
