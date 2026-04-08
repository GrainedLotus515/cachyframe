from __future__ import annotations

from typing import Any

from cachyframe_core.models import CaptureSchemaVersion

from .decoder import CaptureDecoderRegistry


class CachyFrameMitmAddon:
    def __init__(self) -> None:
        self.registry = CaptureDecoderRegistry()

    def response(self, flow: Any) -> None:  # pragma: no cover - exercised via mitmproxy
        schema_version = CaptureSchemaVersion(game_build="unknown", parser_version="0.1.0")
        _ = self.registry.decode(
            message_type="inventory_snapshot",
            payload={},
            schema_version=schema_version,
        )
        # The addon intentionally leaves per-endpoint payload extraction for future iterations.


addons = [CachyFrameMitmAddon()]

