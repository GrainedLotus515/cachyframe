from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx
from cachyframe_core.settings import get_settings

from .certs import ensure_ca_material
from .decoder import CaptureDecoderRegistry
from .proton import render_instructions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CachyFrame Proton proxy helper")
    parser.add_argument(
        "--prefix",
        type=Path,
        default=Path.home() / ".steam/steam/steamapps/compatdata/230410/pfx",
    )
    parser.add_argument("--fixture", type=Path, help="Decode a JSON capture fixture batch")
    parser.add_argument("--post-url", help="Backend base URL to post decoded events to")
    parser.add_argument("--user-hash", help="User hash for backend event ingestion")
    return parser


def main() -> None:
    settings = get_settings()
    parser = build_parser()
    args = parser.parse_args()
    if args.fixture:
        registry = CaptureDecoderRegistry()
        envelopes = json.loads(args.fixture.read_text(encoding="utf-8"))
        events = registry.decode_batch(envelopes)
        decoded_payload = [event.model_dump(mode="json") for event in events]
        print(json.dumps(decoded_payload, indent=2))
        if args.post_url:
            user_hash = args.user_hash or next(
                (
                    event["snapshot"]["user_hash"]
                    for event in decoded_payload
                    if event["kind"] == "inventory_snapshot"
                ),
                settings.user_hash,
            )
            response = httpx.post(
                f"{args.post_url.rstrip('/')}/api/client/v1/capture-events:batch",
                json={"user_hash": user_hash, "events": decoded_payload},
                timeout=30.0,
            )
            response.raise_for_status()
            print(json.dumps(response.json(), indent=2))
        return
    _, cert_path = ensure_ca_material(settings.paths.ca_dir)
    print(
        render_instructions(
            prefix_dir=args.prefix,
            proxy_host=settings.proxy.host,
            proxy_port=settings.proxy.port,
            cert_path=cert_path,
        )
    )


if __name__ == "__main__":
    main()
