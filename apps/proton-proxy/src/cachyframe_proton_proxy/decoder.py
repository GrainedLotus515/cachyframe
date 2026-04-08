from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from cachyframe_core.models import (
    AccountProgressEvent,
    AccountSnapshot,
    CaptureSchemaVersion,
    InventoryDeltaEvent,
    InventoryItem,
    InventorySnapshotEvent,
    MarketRelevantItemEvent,
    NormalizedCaptureEvent,
    OwnedRelic,
    RelicInventoryEvent,
    SessionBoundaryEvent,
    TradeHandshakeEvent,
    TradeRecord,
)

Decoder = Callable[
    [dict[str, Any], CaptureSchemaVersion, dict[str, Any]],
    list[NormalizedCaptureEvent],
]


def _parse_datetime(raw_value: str | None) -> datetime:
    if not raw_value:
        return datetime.now(UTC)
    return datetime.fromisoformat(raw_value.replace("Z", "+00:00"))


class CaptureDecoderRegistry:
    def __init__(self) -> None:
        self._decoders: dict[str, Decoder] = {}
        self.register("inventory_snapshot", self._decode_inventory_snapshot)
        self.register("inventory_delta", self._decode_inventory_delta)
        self.register("relic_inventory", self._decode_relic_inventory)
        self.register("account_progress", self._decode_account_progress)
        self.register("trade_handshake", self._decode_trade_handshake)
        self.register("market_relevant_item", self._decode_market_relevant_item)
        self.register("session_boundary", self._decode_session_boundary)

    def register(self, message_type: str, decoder: Decoder) -> None:
        self._decoders[message_type] = decoder

    def decode(
        self,
        message_type: str,
        payload: dict[str, Any],
        schema_version: CaptureSchemaVersion,
        event_kwargs: dict[str, Any] | None = None,
    ) -> list[NormalizedCaptureEvent]:
        decoder = self._decoders.get(message_type)
        if decoder is None:
            return []
        return decoder(payload, schema_version, event_kwargs or {})

    def decode_envelope(self, envelope: dict[str, Any]) -> list[NormalizedCaptureEvent]:
        schema_version = CaptureSchemaVersion(
            game_build=envelope.get("game_build", "unknown"),
            parser_version=envelope.get("parser_version", "0.1.0"),
            captured_at=_parse_datetime(envelope.get("captured_at")),
        )
        event_kwargs = {
            "occurred_at": _parse_datetime(envelope.get("occurred_at")),
            "source": envelope.get("source", "tls_capture"),
            "raw_reference": envelope.get("raw_reference"),
        }
        return self.decode(
            envelope["message_type"],
            envelope.get("payload", {}),
            schema_version,
            event_kwargs=event_kwargs,
        )

    def decode_batch(self, envelopes: list[dict[str, Any]]) -> list[NormalizedCaptureEvent]:
        events: list[NormalizedCaptureEvent] = []
        for envelope in envelopes:
            events.extend(self.decode_envelope(envelope))
        return events

    def _decode_inventory_snapshot(
        self,
        payload: dict[str, Any],
        schema_version: CaptureSchemaVersion,
        event_kwargs: dict[str, Any],
    ) -> list[NormalizedCaptureEvent]:
        snapshot = AccountSnapshot.model_validate(payload)
        return [
            InventorySnapshotEvent(
                schema_version=schema_version,
                snapshot=snapshot,
                **event_kwargs,
            )
        ]

    def _decode_inventory_delta(
        self,
        payload: dict[str, Any],
        schema_version: CaptureSchemaVersion,
        event_kwargs: dict[str, Any],
    ) -> list[NormalizedCaptureEvent]:
        items = [InventoryItem.model_validate(item) for item in payload.get("items", [])]
        return [InventoryDeltaEvent(schema_version=schema_version, items=items, **event_kwargs)]

    def _decode_relic_inventory(
        self,
        payload: dict[str, Any],
        schema_version: CaptureSchemaVersion,
        event_kwargs: dict[str, Any],
    ) -> list[NormalizedCaptureEvent]:
        relics = [OwnedRelic.model_validate(relic) for relic in payload.get("relics", [])]
        return [RelicInventoryEvent(schema_version=schema_version, relics=relics, **event_kwargs)]

    def _decode_account_progress(
        self,
        payload: dict[str, Any],
        schema_version: CaptureSchemaVersion,
        event_kwargs: dict[str, Any],
    ) -> list[NormalizedCaptureEvent]:
        return [
            AccountProgressEvent(
                schema_version=schema_version,
                mastery_rank=payload.get("mastery_rank", 0),
                metadata=payload.get("metadata", {}),
                **event_kwargs,
            )
        ]

    def _decode_trade_handshake(
        self,
        payload: dict[str, Any],
        schema_version: CaptureSchemaVersion,
        event_kwargs: dict[str, Any],
    ) -> list[NormalizedCaptureEvent]:
        trade = TradeRecord.model_validate(payload.get("trade", {}))
        return [TradeHandshakeEvent(schema_version=schema_version, trade=trade, **event_kwargs)]

    def _decode_market_relevant_item(
        self,
        payload: dict[str, Any],
        schema_version: CaptureSchemaVersion,
        event_kwargs: dict[str, Any],
    ) -> list[NormalizedCaptureEvent]:
        items = [InventoryItem.model_validate(item) for item in payload.get("items", [])]
        return [MarketRelevantItemEvent(schema_version=schema_version, items=items, **event_kwargs)]

    def _decode_session_boundary(
        self,
        payload: dict[str, Any],
        schema_version: CaptureSchemaVersion,
        event_kwargs: dict[str, Any],
    ) -> list[NormalizedCaptureEvent]:
        return [
            SessionBoundaryEvent(
                schema_version=schema_version,
                phase=payload.get("phase", "loading"),
                metadata=payload.get("metadata", {}),
                **event_kwargs,
            )
        ]
