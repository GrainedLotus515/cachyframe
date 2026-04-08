from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any

import orjson


class FileCache:
    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _path_for_key(self, key: str) -> Path:
        return self._cache_dir / f"{sha256(key.encode('utf-8')).hexdigest()}.json"

    def get(self, key: str, ttl_seconds: int) -> Any | None:
        path = self._path_for_key(key)
        if not path.exists():
            return None
        age = datetime.now(UTC) - datetime.fromtimestamp(path.stat().st_mtime, UTC)
        if age > timedelta(seconds=ttl_seconds):
            return None
        return orjson.loads(path.read_bytes())

    def set(self, key: str, payload: Any) -> None:
        path = self._path_for_key(key)
        path.write_bytes(orjson.dumps(payload))

