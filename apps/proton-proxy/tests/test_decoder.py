from __future__ import annotations

import json
from pathlib import Path

from cachyframe_core.models import CaptureEventKind
from cachyframe_proton_proxy.decoder import CaptureDecoderRegistry


def test_decoder_registry_decodes_fixture_batch() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "capture_batch.json"
    envelopes = json.loads(fixture_path.read_text(encoding="utf-8"))
    registry = CaptureDecoderRegistry()
    events = registry.decode_batch(envelopes)

    assert len(events) == 6
    assert [event.kind for event in events] == [
        CaptureEventKind.INVENTORY_SNAPSHOT,
        CaptureEventKind.RELIC_INVENTORY,
        CaptureEventKind.ACCOUNT_PROGRESS,
        CaptureEventKind.TRADE_HANDSHAKE,
        CaptureEventKind.MARKET_RELEVANT_ITEM,
        CaptureEventKind.SESSION_BOUNDARY,
    ]
    assert events[0].source == "tls_capture"
    assert events[1].occurred_at.isoformat().startswith("2026-04-08T05:00:01")
