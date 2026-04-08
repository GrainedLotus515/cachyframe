from __future__ import annotations

from cachyframe_core.models import (
    AccountProgressEvent,
    AccountSnapshot,
    InventoryDeltaEvent,
    InventorySnapshotEvent,
    MarketRelevantItemEvent,
    RelicInventoryEvent,
)


class AccountSnapshotReconciler:
    def __init__(self, seed_snapshot: AccountSnapshot | None = None) -> None:
        self._snapshot = seed_snapshot or AccountSnapshot(
            user_hash="local-user",
            source="reconciler",
        )

    @property
    def snapshot(self) -> AccountSnapshot:
        return self._snapshot

    def apply_event(
        self,
        event: InventorySnapshotEvent
        | InventoryDeltaEvent
        | RelicInventoryEvent
        | AccountProgressEvent
        | MarketRelevantItemEvent,
    ) -> AccountSnapshot:
        if isinstance(event, InventorySnapshotEvent):
            self._snapshot = event.snapshot
        elif isinstance(event, InventoryDeltaEvent):
            items = {item.item_id: item for item in self._snapshot.items}
            for item in event.items:
                items[item.item_id] = item
            self._snapshot.items = sorted(items.values(), key=lambda item: item.name.lower())
        elif isinstance(event, RelicInventoryEvent):
            self._snapshot.relics = sorted(
                event.relics,
                key=lambda relic: (int(relic.tier), relic.code),
            )
        elif isinstance(event, AccountProgressEvent):
            self._snapshot.mastery_rank = event.mastery_rank
            self._snapshot.metadata.update(event.metadata)
        elif isinstance(event, MarketRelevantItemEvent):
            tradable_ids = {item.item_id for item in event.items}
            for item in self._snapshot.items:
                if item.item_id in tradable_ids:
                    item.tradable = True
        self._snapshot.captured_at = event.occurred_at
        return self._snapshot
