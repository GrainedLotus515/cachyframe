from __future__ import annotations

from datetime import UTC, datetime
from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class RelicTier(IntEnum):
    LITH = 0
    MESO = 1
    NEO = 2
    AXI = 3
    REQUIEM = 4


class RelicRefinement(IntEnum):
    INTACT = 0
    EXCEPTIONAL = 1
    FLAWLESS = 2
    RADIANT = 3


class PublicLinkParts(IntFlag):
    NONE = 0
    TRADES = 1
    PLATINUM = 2
    DUCATS = 4
    ENDO = 8
    CREDITS = 16
    ACCOUNT_DATA = 32
    AYA = 64
    RELICS = 128


class TradeClassification(IntEnum):
    SALE = 0
    PURCHASE = 1
    TRADE = 2


class CaptureEventKind(StrEnum):
    INVENTORY_SNAPSHOT = "inventory_snapshot"
    INVENTORY_DELTA = "inventory_delta"
    RELIC_INVENTORY = "relic_inventory"
    ACCOUNT_PROGRESS = "account_progress"
    TRADE_HANDSHAKE = "trade_handshake"
    MARKET_RELEVANT_ITEM = "market_relevant_item"
    SESSION_BOUNDARY = "session_boundary"


class OverlayKind(StrEnum):
    RELIC_RECOMMENDATION = "relic_recommendation"
    RELIC_REWARDS = "relic_rewards"
    RIVEN_CHAT = "riven_chat"
    RIVEN_REROLL = "riven_reroll"


class OrderedItem(Model):
    name: str
    display_name: str | None = None
    quantity: int = Field(default=1, ge=1)
    rank: int = 0


class InventoryItem(Model):
    item_id: str
    unique_name: str | None = None
    name: str
    quantity: int = Field(default=1, ge=0)
    category: str | None = None
    type: str | None = None
    tradable: bool = False
    mastered: bool = False
    owned: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class OwnedRelic(Model):
    tier: RelicTier
    code: str = Field(min_length=1, max_length=3)
    refinement: RelicRefinement = RelicRefinement.INTACT
    quantity: int = Field(default=1, ge=0)
    is_vaulted: bool = False
    favorite: bool = False


class FoundryItemState(Model):
    item_id: str
    name: str
    item_type: str | None = None
    mastered: bool = False
    owned: bool = False
    vaulted: bool = False
    ready_to_build: bool = False
    enough_mastery: bool = True
    used_for_crafting: bool = False
    favorite: bool = False
    helminth_done: bool = False
    contains_archon_shards: bool = False
    available_components: list[str] = Field(default_factory=list)


class CraftTreeNode(Model):
    item_id: str
    name: str
    quantity: int = Field(default=1, ge=1)
    available_quantity: int = Field(default=0, ge=0)
    required_resources: dict[str, int] = Field(default_factory=dict)
    children: list[CraftTreeNode] = Field(default_factory=list)


class StatsPoint(Model):
    ts: datetime = Field(default_factory=utc_now)
    plat: int = 0
    credits: int = 0
    endo: int = 0
    ducats: int = 0
    aya: int = 0
    relic_opened: int = 0
    trades: int = 0
    mr: int = 0
    percentage_completion: int = 0


class TradeRecord(Model):
    ts: datetime = Field(default_factory=utc_now)
    tx: list[OrderedItem] = Field(default_factory=list)
    rx: list[OrderedItem] = Field(default_factory=list)
    user: str | None = None
    type: TradeClassification = TradeClassification.TRADE
    total_plat: int | None = None


class PublicLink(Model):
    id: str = Field(default_factory=lambda: str(uuid4()))
    token: str
    user_hash: str
    parts: int
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime
    revoked_at: datetime | None = None
    username_when_public: str | None = None


class MarketOrder(Model):
    id: str
    item_id: str
    item_name: str
    order_type: Literal["buy", "sell"]
    quantity: int = Field(default=1, ge=0)
    platinum: int = Field(default=0, ge=0)
    visible: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MarketContract(Model):
    id: str
    contract_type: str
    item_name: str
    visible: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class RivenMod(Model):
    id: str
    weapon_name: str
    positives: list[str] = Field(default_factory=list)
    negative: str | None = None
    grade: str | None = None
    disposition: float | None = None
    rerolls: int = 0
    mastery_rank: int = 0
    price_estimate: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RivenSearchQuery(Model):
    weapon_name: str | None = None
    positives: list[str] = Field(default_factory=list)
    negative: str | None = None
    min_price: int | None = None
    max_price: int | None = None
    max_rerolls: int | None = None


class SniperSubscription(Model):
    id: str = Field(default_factory=lambda: str(uuid4()))
    enabled: bool = True
    discord_webhook_url: str | None = None
    query: RivenSearchQuery
    created_at: datetime = Field(default_factory=utc_now)


class OverlayTrigger(Model):
    kind: OverlayKind
    source: str
    triggered_at: datetime = Field(default_factory=utc_now)
    payload: dict[str, Any] = Field(default_factory=dict)


class OcrCalibration(Model):
    resolution_width: int = 1920
    resolution_height: int = 1080
    ui_scale: float = 1.0
    theme: str = "default"
    calibrated_at: datetime = Field(default_factory=utc_now)


class CollectorConfidence(Model):
    domain: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)


class CaptureSchemaVersion(Model):
    game_build: str
    parser_version: str
    captured_at: datetime = Field(default_factory=utc_now)


class AccountSnapshot(Model):
    user_hash: str
    secret_token: str | None = None
    username: str | None = None
    platform: str = "pc"
    captured_at: datetime = Field(default_factory=utc_now)
    source: str = "tls_capture"
    mastery_rank: int = 0
    items: list[InventoryItem] = Field(default_factory=list)
    relics: list[OwnedRelic] = Field(default_factory=list)
    foundry_states: list[FoundryItemState] = Field(default_factory=list)
    confidences: list[CollectorConfidence] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class NormalizedCaptureEvent(Model):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    kind: CaptureEventKind
    occurred_at: datetime = Field(default_factory=utc_now)
    schema_version: CaptureSchemaVersion
    source: str = "tls_capture"
    raw_reference: str | None = None


class InventorySnapshotEvent(NormalizedCaptureEvent):
    kind: Literal[CaptureEventKind.INVENTORY_SNAPSHOT] = CaptureEventKind.INVENTORY_SNAPSHOT
    snapshot: AccountSnapshot


class InventoryDeltaEvent(NormalizedCaptureEvent):
    kind: Literal[CaptureEventKind.INVENTORY_DELTA] = CaptureEventKind.INVENTORY_DELTA
    items: list[InventoryItem] = Field(default_factory=list)


class RelicInventoryEvent(NormalizedCaptureEvent):
    kind: Literal[CaptureEventKind.RELIC_INVENTORY] = CaptureEventKind.RELIC_INVENTORY
    relics: list[OwnedRelic] = Field(default_factory=list)


class AccountProgressEvent(NormalizedCaptureEvent):
    kind: Literal[CaptureEventKind.ACCOUNT_PROGRESS] = CaptureEventKind.ACCOUNT_PROGRESS
    mastery_rank: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class TradeHandshakeEvent(NormalizedCaptureEvent):
    kind: Literal[CaptureEventKind.TRADE_HANDSHAKE] = CaptureEventKind.TRADE_HANDSHAKE
    trade: TradeRecord


class MarketRelevantItemEvent(NormalizedCaptureEvent):
    kind: Literal[CaptureEventKind.MARKET_RELEVANT_ITEM] = CaptureEventKind.MARKET_RELEVANT_ITEM
    items: list[InventoryItem] = Field(default_factory=list)


class SessionBoundaryEvent(NormalizedCaptureEvent):
    kind: Literal[CaptureEventKind.SESSION_BOUNDARY] = CaptureEventKind.SESSION_BOUNDARY
    phase: Literal["start", "end", "loading"]
    metadata: dict[str, Any] = Field(default_factory=dict)


type CaptureEvent = Annotated[
    InventorySnapshotEvent
    | InventoryDeltaEvent
    | RelicInventoryEvent
    | AccountProgressEvent
    | TradeHandshakeEvent
    | MarketRelevantItemEvent
    | SessionBoundaryEvent,
    Field(discriminator="kind"),
]


CraftTreeNode.model_rebuild()
