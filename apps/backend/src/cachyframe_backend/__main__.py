from __future__ import annotations

import uvicorn
from cachyframe_core.settings import get_settings

from .app import create_app


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        create_app(),
        host=settings.backend.host,
        port=settings.backend.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()

