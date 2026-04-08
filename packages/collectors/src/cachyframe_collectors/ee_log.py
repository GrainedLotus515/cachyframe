from __future__ import annotations

import asyncio
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(slots=True)
class EELogEvent:
    kind: str
    ts: datetime
    line: str
    metadata: dict[str, str]


class EELogTailer:
    SESSION_START = re.compile(r"Game \[Info\]: Initializing world")
    SESSION_END = re.compile(r"Game \[Info\]: Main shutdown")
    TRADE_MESSAGE = re.compile(r"trade", re.IGNORECASE)
    RIVEN_MESSAGE = re.compile(r"riven", re.IGNORECASE)
    RELIC_REWARD = re.compile(r"relic", re.IGNORECASE)

    def __init__(self, log_path: Path, poll_interval: float = 0.5) -> None:
        self._log_path = log_path
        self._poll_interval = poll_interval

    def parse_line(self, line: str) -> EELogEvent | None:
        ts = datetime.now(UTC)
        if self.SESSION_START.search(line):
            return EELogEvent(kind="session_start", ts=ts, line=line, metadata={})
        if self.SESSION_END.search(line):
            return EELogEvent(kind="session_end", ts=ts, line=line, metadata={})
        if self.TRADE_MESSAGE.search(line):
            return EELogEvent(kind="trade", ts=ts, line=line, metadata={})
        if self.RIVEN_MESSAGE.search(line):
            return EELogEvent(kind="riven", ts=ts, line=line, metadata={})
        if self.RELIC_REWARD.search(line):
            return EELogEvent(kind="relic", ts=ts, line=line, metadata={})
        return None

    async def iter_events(self) -> AsyncIterator[EELogEvent]:
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_path.touch(exist_ok=True)
        with self._log_path.open("r", encoding="utf-8", errors="ignore") as handle:
            handle.seek(0, 2)
            while True:
                line = handle.readline()
                if not line:
                    await asyncio.sleep(self._poll_interval)
                    continue
                event = self.parse_line(line.rstrip())
                if event is not None:
                    yield event

