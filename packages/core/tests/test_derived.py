from cachyframe_core.derived import (
    build_foundry_summary,
    build_inventory_summary,
    build_relic_summary,
    build_snapshot_summary,
)
from cachyframe_core.models import (
    AccountSnapshot,
    FoundryItemState,
    InventoryItem,
    OwnedRelic,
    RelicRefinement,
    RelicTier,
)


def test_snapshot_derived_summaries() -> None:
    snapshot = AccountSnapshot(
        user_hash="user-1",
        mastery_rank=12,
        items=[
            InventoryItem(item_id="a", name="Alpha", quantity=2, tradable=True),
            InventoryItem(item_id="b", name="Beta", quantity=1, tradable=False),
        ],
        relics=[
            OwnedRelic(
                tier=RelicTier.LITH,
                code="A1",
                refinement=RelicRefinement.INTACT,
                quantity=3,
            ),
            OwnedRelic(
                tier=RelicTier.MESO,
                code="B2",
                refinement=RelicRefinement.RADIANT,
                quantity=5,
            ),
        ],
        foundry_states=[
            FoundryItemState(
                item_id="wf",
                name="Warframe",
                owned=True,
                mastered=False,
                ready_to_build=True,
            )
        ],
    )

    snapshot_summary = build_snapshot_summary(snapshot)
    foundry_summary = build_foundry_summary(snapshot)
    inventory_summary = build_inventory_summary(snapshot, tradable_only=True)
    relic_summary = build_relic_summary(snapshot)

    assert snapshot_summary.total_owned_quantity == 3
    assert snapshot_summary.ready_to_build_count == 1
    assert foundry_summary.ready_to_build == 1
    assert inventory_summary.total_unique == 1
    assert relic_summary.total_quantity == 8
