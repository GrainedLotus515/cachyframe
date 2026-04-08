from __future__ import annotations

from collections import defaultdict
from typing import Any

from pydantic import Field

from .models import AccountSnapshot, FoundryItemState, InventoryItem, Model, OwnedRelic, RelicTier


class SnapshotSummary(Model):
    user_hash: str
    captured_at: str
    source: str
    mastery_rank: int
    total_unique_items: int
    total_owned_quantity: int
    total_tradable_unique: int
    total_tradable_quantity: int
    total_relic_quantity: int
    distinct_relics: int
    ready_to_build_count: int
    mastered_count: int
    unmastered_owned_count: int


class FoundrySummary(Model):
    total: int
    owned: int
    mastered: int
    ready_to_build: int
    favorites: int
    vaulted: int
    items: list[FoundryItemState] = Field(default_factory=list)


class InventorySummary(Model):
    total_unique: int
    total_quantity: int
    tradable_unique: int
    tradable_quantity: int
    items: list[InventoryItem] = Field(default_factory=list)


class RelicTierSummary(Model):
    tier: RelicTier
    total_quantity: int
    distinct_relics: int


class RelicSummary(Model):
    total_quantity: int
    distinct_relics: int
    tiers: list[RelicTierSummary] = Field(default_factory=list)
    relics: list[OwnedRelic] = Field(default_factory=list)


class WorldstateSummary(Model):
    timestamp: str | None = None
    alerts: int = 0
    events: int = 0
    fissures: int = 0
    invasions: int = 0
    news: int = 0
    sorties: int = 0
    steel_path_active: bool = False
    active_arbitration: str | None = None


class DashboardSummary(Model):
    worldstate: WorldstateSummary | None = None
    snapshot: SnapshotSummary | None = None
    analytics: dict[str, int | float] = Field(default_factory=dict)


def build_snapshot_summary(snapshot: AccountSnapshot) -> SnapshotSummary:
    tradable_items = [item for item in snapshot.items if item.tradable]
    owned_foundry = [item for item in snapshot.foundry_states if item.owned]
    return SnapshotSummary(
        user_hash=snapshot.user_hash,
        captured_at=snapshot.captured_at.isoformat(),
        source=snapshot.source,
        mastery_rank=snapshot.mastery_rank,
        total_unique_items=len(snapshot.items),
        total_owned_quantity=sum(item.quantity for item in snapshot.items),
        total_tradable_unique=len(tradable_items),
        total_tradable_quantity=sum(item.quantity for item in tradable_items),
        total_relic_quantity=sum(relic.quantity for relic in snapshot.relics),
        distinct_relics=len(snapshot.relics),
        ready_to_build_count=sum(1 for item in snapshot.foundry_states if item.ready_to_build),
        mastered_count=sum(1 for item in snapshot.foundry_states if item.mastered),
        unmastered_owned_count=sum(1 for item in owned_foundry if not item.mastered),
    )


def build_foundry_summary(snapshot: AccountSnapshot) -> FoundrySummary:
    items = sorted(snapshot.foundry_states, key=lambda item: item.name.lower())
    return FoundrySummary(
        total=len(items),
        owned=sum(1 for item in items if item.owned),
        mastered=sum(1 for item in items if item.mastered),
        ready_to_build=sum(1 for item in items if item.ready_to_build),
        favorites=sum(1 for item in items if item.favorite),
        vaulted=sum(1 for item in items if item.vaulted),
        items=items,
    )


def build_inventory_summary(
    snapshot: AccountSnapshot,
    *,
    tradable_only: bool = False,
) -> InventorySummary:
    items = sorted(snapshot.items, key=lambda item: item.name.lower())
    filtered_items = [item for item in items if item.tradable] if tradable_only else items
    tradable_items = [item for item in items if item.tradable]
    return InventorySummary(
        total_unique=len(filtered_items),
        total_quantity=sum(item.quantity for item in filtered_items),
        tradable_unique=len(tradable_items),
        tradable_quantity=sum(item.quantity for item in tradable_items),
        items=filtered_items,
    )


def build_relic_summary(snapshot: AccountSnapshot) -> RelicSummary:
    tier_totals: dict[RelicTier, dict[str, int]] = defaultdict(
        lambda: {"total_quantity": 0, "distinct_relics": 0}
    )
    for relic in snapshot.relics:
        tier_totals[relic.tier]["total_quantity"] += relic.quantity
        tier_totals[relic.tier]["distinct_relics"] += 1
    tiers = [
        RelicTierSummary(
            tier=tier,
            total_quantity=payload["total_quantity"],
            distinct_relics=payload["distinct_relics"],
        )
        for tier, payload in sorted(tier_totals.items(), key=lambda item: int(item[0]))
    ]
    return RelicSummary(
        total_quantity=sum(relic.quantity for relic in snapshot.relics),
        distinct_relics=len(snapshot.relics),
        tiers=tiers,
        relics=sorted(snapshot.relics, key=lambda relic: (int(relic.tier), relic.code)),
    )


def build_worldstate_summary(payload: dict[str, Any]) -> WorldstateSummary:
    arbitration = payload.get("arbitration")
    return WorldstateSummary(
        timestamp=payload.get("timestamp"),
        alerts=len(payload.get("alerts", [])),
        events=len(payload.get("events", [])),
        fissures=len(payload.get("fissures", [])),
        invasions=len(payload.get("invasions", [])),
        news=len(payload.get("news", [])),
        sorties=1 if payload.get("sortie") else 0,
        steel_path_active=bool(payload.get("steelPath")),
        active_arbitration=arbitration.get("node") if isinstance(arbitration, dict) else None,
    )

