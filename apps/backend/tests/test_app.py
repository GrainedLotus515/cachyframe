from __future__ import annotations

from pathlib import Path

from cachyframe_backend.app import create_app
from cachyframe_core.settings import get_settings
from fastapi.testclient import TestClient


def _configure_test_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(
        "CACHYFRAME_DATABASE__BACKEND_URL",
        f"sqlite+aiosqlite:///{tmp_path / 'backend.db'}",
    )
    monkeypatch.setenv(
        "CACHYFRAME_DATABASE__LOCAL_URL",
        f"sqlite+aiosqlite:///{tmp_path / 'local.db'}",
    )
    monkeypatch.setenv("CACHYFRAME_USER_HASH", "test-user")
    get_settings.cache_clear()


def test_healthz(tmp_path: Path, monkeypatch) -> None:
    _configure_test_env(tmp_path, monkeypatch)
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    get_settings.cache_clear()


def test_snapshot_driven_routes(tmp_path: Path, monkeypatch) -> None:
    _configure_test_env(tmp_path, monkeypatch)
    app = create_app()
    snapshot = {
        "snapshot": {
            "user_hash": "test-user",
            "secret_token": "secret",
            "mastery_rank": 18,
            "items": [
                {
                    "item_id": "forma_blueprint",
                    "name": "Forma Blueprint",
                    "quantity": 4,
                    "tradable": True,
                },
                {
                    "item_id": "endo",
                    "name": "Endo",
                    "quantity": 1200,
                    "tradable": False,
                },
            ],
            "relics": [
                {
                    "tier": 0,
                    "code": "A1",
                    "refinement": 0,
                    "quantity": 3,
                }
            ],
            "foundry_states": [
                {
                    "item_id": "wisp_prime",
                    "name": "Wisp Prime",
                    "owned": True,
                    "mastered": False,
                    "ready_to_build": True,
                }
            ],
        }
    }
    with TestClient(app) as client:
        post_response = client.post("/api/client/v1/account/snapshots", json=snapshot)
        assert post_response.status_code == 200

        foundry_response = client.get("/api/client/v1/foundry", params={"user_hash": "test-user"})
        inventory_response = client.get(
            "/api/client/v1/inventory",
            params={"user_hash": "test-user", "tradable_only": True},
        )
        relic_response = client.get("/api/client/v1/relics", params={"user_hash": "test-user"})
        dashboard_response = client.get(
            "/api/client/v1/dashboard",
            params={"user_hash": "test-user"},
        )

    assert foundry_response.status_code == 200
    assert foundry_response.json()["ready_to_build"] == 1
    assert inventory_response.status_code == 200
    assert inventory_response.json()["total_unique"] == 1
    assert relic_response.status_code == 200
    assert relic_response.json()["total_quantity"] == 3
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["snapshot"]["mastery_rank"] == 18
    get_settings.cache_clear()


def test_capture_event_ingestion_route(tmp_path: Path, monkeypatch) -> None:
    _configure_test_env(tmp_path, monkeypatch)
    app = create_app()
    payload = {
        "user_hash": "test-user",
        "events": [
            {
                "kind": "inventory_snapshot",
                "schema_version": {
                    "game_build": "38.1.0",
                    "parser_version": "0.1.0",
                },
                "snapshot": {
                    "user_hash": "test-user",
                    "mastery_rank": 10,
                    "items": [
                        {
                            "item_id": "forma_blueprint",
                            "name": "Forma Blueprint",
                            "quantity": 2,
                        }
                    ],
                },
            },
            {
                "kind": "relic_inventory",
                "schema_version": {
                    "game_build": "38.1.0",
                    "parser_version": "0.1.0",
                },
                "relics": [
                    {
                        "tier": 0,
                        "code": "A1",
                        "refinement": 0,
                        "quantity": 4,
                    }
                ],
            },
            {
                "kind": "trade_handshake",
                "schema_version": {
                    "game_build": "38.1.0",
                    "parser_version": "0.1.0",
                },
                "trade": {
                    "user": "Trader",
                    "total_plat": 20,
                    "tx": [{"name": "Forma Blueprint", "quantity": 1}],
                    "rx": [{"name": "Platinum", "quantity": 20}],
                },
            },
            {
                "kind": "session_boundary",
                "schema_version": {
                    "game_build": "38.1.0",
                    "parser_version": "0.1.0",
                },
                "phase": "start",
                "metadata": {"zone": "Orbiter"},
            },
        ],
    }
    with TestClient(app) as client:
        ingest_response = client.post("/api/client/v1/capture-events:batch", json=payload)
        assert ingest_response.status_code == 200

        current_snapshot = client.get(
            "/api/client/v1/account/current",
            params={"user_hash": "test-user"},
        )
        capture_events = client.get(
            "/api/client/v1/capture-events",
            params={"user_hash": "test-user"},
        )
        analytics = client.get(
            "/api/client/v1/analytics/overview",
            params={"user_hash": "test-user"},
        )

    body = ingest_response.json()
    assert body["accepted_events"] == 4
    assert body["accepted_trades"] == 1
    assert current_snapshot.status_code == 200
    assert current_snapshot.json()["metadata"]["last_session_phase"] == "start"
    assert capture_events.status_code == 200
    assert len(capture_events.json()) == 4
    assert analytics.status_code == 200
    assert analytics.json()["trade_count"] == 1
    get_settings.cache_clear()
