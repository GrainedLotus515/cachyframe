from datetime import UTC, datetime

from cachyframe_collectors.reconciliation import AccountSnapshotReconciler
from cachyframe_core.models import (
    AccountSnapshot,
    CaptureSchemaVersion,
    InventoryDeltaEvent,
    InventoryItem,
)


def test_reconciler_applies_inventory_delta() -> None:
    reconciler = AccountSnapshotReconciler(
        AccountSnapshot(
            user_hash="u1",
            items=[InventoryItem(item_id="item-1", name="A", quantity=1)],
        )
    )
    event = InventoryDeltaEvent(
        occurred_at=datetime.now(UTC),
        schema_version=CaptureSchemaVersion(game_build="1", parser_version="1"),
        items=[InventoryItem(item_id="item-2", name="B", quantity=2)],
    )
    snapshot = reconciler.apply_event(event)
    assert {item.item_id for item in snapshot.items} == {"item-1", "item-2"}

