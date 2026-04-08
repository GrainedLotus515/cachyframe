from __future__ import annotations

import asyncio
import json

from cachyframe_core.settings import get_settings

from .jobs import WorkerJobs


async def _run() -> None:
    settings = get_settings()
    jobs = WorkerJobs()
    await jobs.startup()
    worldstate = await jobs.refresh_worldstate()
    print(
        json.dumps(
            {
                "timestamp": worldstate.get("timestamp"),
                "events": len(worldstate.get("events", [])),
                "platform": settings.platform,
            },
            indent=2,
        )
    )


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()

