from cachyframe_core.compat import encode_relic_inventory
from cachyframe_core.models import OwnedRelic, RelicRefinement, RelicTier


def test_encode_relic_inventory_layout() -> None:
    payload = encode_relic_inventory(
        [
            OwnedRelic(
                tier=RelicTier.LITH,
                code="A1",
                refinement=RelicRefinement.INTACT,
                quantity=7,
            )
        ]
    )
    assert len(payload) == 4 + 9
    assert payload[:4] == b"\x01\x00\x00\x00"
    assert payload[4] == 0
    assert payload[5] == 0
    assert payload[6:9] == b"A1\x00"

