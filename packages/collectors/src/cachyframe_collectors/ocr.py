from __future__ import annotations

from pathlib import Path
from typing import Any

from cachyframe_core.models import OcrCalibration, OverlayKind, OverlayTrigger

try:
    from rapidocr_onnxruntime import RapidOCR
except ImportError:  # pragma: no cover - optional at import time
    RapidOCR = None


class OcrService:
    def __init__(self, calibration: OcrCalibration | None = None) -> None:
        self._calibration = calibration or OcrCalibration()
        self._engine = RapidOCR() if RapidOCR is not None else None

    @property
    def calibration(self) -> OcrCalibration:
        return self._calibration

    def detect_text(self, image_path: Path) -> list[str]:
        if self._engine is None:
            return []
        result, _ = self._engine(str(image_path))
        return [row[1] for row in result or []]

    def detect_overlay_trigger(self, image_path: Path, source: str) -> OverlayTrigger | None:
        tokens = {token.lower() for token in self.detect_text(image_path)}
        if {"riven", "reroll"} & tokens:
            return OverlayTrigger(kind=OverlayKind.RIVEN_REROLL, source=source)
        if {"relic", "reward"} & tokens:
            return OverlayTrigger(kind=OverlayKind.RELIC_REWARDS, source=source)
        return None

    def detect_relic_rewards(self, image_path: Path) -> dict[str, Any]:
        return {"text": self.detect_text(image_path), "calibration": self._calibration.model_dump()}

