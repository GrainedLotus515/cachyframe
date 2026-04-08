# CachyFrame

CachyFrame is a Linux-first, AlecaFrame-compatible Warframe companion workspace.
It combines a FastAPI backend, a PySide6 desktop shell, shared domain/storage
packages, and a Proton/Wine helper for capture-driven account state ingestion.

The current repository already includes the backend API, persistence layer,
upstream clients, capture event decoding, and a desktop shell that reads backend
state. Some surfaces are still scaffolding: overlay UX is basic, and live
`mitmproxy` payload extraction is not fully implemented yet.

## Features

Implemented today:

- FastAPI backend with health, worldstate, dashboard, foundry, inventory, relic,
  analytics, public-link, sniper-subscription, diagnostics, and capture-ingest
  endpoints.
- AlecaFrame-style stats endpoints under `/api/stats/*`, including public stats
  reads and binary relic inventory export.
- SQLite-backed persistence for snapshots, trades, stats points, normalized
  capture events, public links, sniper subscriptions, and diagnostics uploads.
- PySide6 desktop shell with tabs for Foundry, Inventory, Mastery Helper, Relic
  Planner, Rivens, and Stats, all backed by the running API.
- Proton helper CLI that can generate a local CA, print Proton launch
  environment variables, decode fixture batches, and post normalized capture
  events to the backend.
- Local collector primitives for `EE.log` tailing, OCR-based overlay trigger
  detection, and account snapshot reconciliation.
- Cached upstream clients for `warframestat.us`, `warframe.market`, and the
  official Warframe PublicExport index/drop tables.
- Worker job entrypoints for worldstate refresh, riven refresh, export refresh,
  and analytics materialization.

Still in progress:

- Live response extraction inside the `mitmproxy` addon is placeholder code.
- Desktop tabs currently render backend JSON/state summaries rather than final
  product UI.
- Overlay windows exist as scaffolding and are not fully wired to collectors.

## Workspace Layout

- `apps/backend`: FastAPI app and compatibility/client APIs.
- `apps/desktop`: PySide6 shell that displays backend state and overlay
  scaffolding.
- `apps/proton-proxy`: Proton/Wine helper CLI, local CA generation, decoder
  registry, and `mitmproxy` addon stub.
- `apps/worker`: one-shot worker entrypoints for background jobs.
- `packages/core`: shared settings, domain models, AlecaFrame compatibility
  types, and derived summaries.
- `packages/collectors`: `EE.log` tailing, OCR services, and snapshot
  reconciliation.
- `packages/data-sources`: cached clients for public Warframe APIs.
- `packages/storage`: SQLAlchemy models and repository APIs.
- `packages/ui`: reusable Qt widgets and overlay window primitives.

## Requirements

- Linux
- Python 3.12
- `uv`

Notes:

- Overlay work currently targets X11/XWayland.
- The default Proton prefix assumes Warframe app ID `230410`.
- Qt/OCR features may require the usual system GUI/runtime libraries for your
  distro.

## Configuration

CachyFrame uses `pydantic-settings` with the `CACHYFRAME_` prefix and `__` as
the nested delimiter.

Common settings:

| Variable | Default | Purpose |
| --- | --- | --- |
| `CACHYFRAME_USER_HASH` | `local-user` | Default user identity for local ingestion and desktop queries. |
| `CACHYFRAME_SECRET_TOKEN` | `dev-secret` | Secret token used for AlecaFrame-compatible private stats reads. |
| `CACHYFRAME_PLATFORM` | `pc` | Upstream platform for worldstate and riven data. |
| `CACHYFRAME_BACKEND__HOST` | `127.0.0.1` | Backend bind host. |
| `CACHYFRAME_BACKEND__PORT` | `8010` | Backend bind port. |
| `CACHYFRAME_DESKTOP__BACKEND_URL` | `http://127.0.0.1:8010` | Backend base URL used by the desktop shell. |
| `CACHYFRAME_DATABASE__BACKEND_URL` | `sqlite+aiosqlite:///./cachyframe-backend.db` | Database used by the backend and worker. |
| `CACHYFRAME_DATABASE__LOCAL_URL` | `sqlite+aiosqlite:///./cachyframe.db` | Local database URL for non-backend consumers. |
| `CACHYFRAME_PROXY__HOST` | `127.0.0.1` | Proxy host used in generated Proton instructions. |
| `CACHYFRAME_PROXY__PORT` | `8899` | Proxy port used in generated Proton instructions. |

Runtime directories are created automatically under:

- `~/.config/cachyframe`
- `~/.local/share/cachyframe`
- `~/.cache/cachyframe`

## Setup

Install dependencies for the full workspace:

```bash
uv sync --all-packages --group dev
```

If you want a stable local identity, export a user hash before starting the
apps:

```bash
export CACHYFRAME_USER_HASH=local-user
```

## How To Use

### 1. Start the backend

The backend auto-creates its schema in the configured database on startup.

```bash
uv run --package cachyframe-backend cachyframe-backend
```

Health check:

```bash
curl http://127.0.0.1:8010/healthz
```

### 2. Seed or update account state

You can post a snapshot directly to the backend:

```bash
curl -X POST http://127.0.0.1:8010/api/client/v1/account/snapshots \
  -H 'content-type: application/json' \
  -d '{
    "snapshot": {
      "user_hash": "local-user",
      "mastery_rank": 18,
      "items": [
        {
          "item_id": "forma_blueprint",
          "name": "Forma Blueprint",
          "quantity": 4,
          "tradable": true
        },
        {
          "item_id": "endo",
          "name": "Endo",
          "quantity": 1200,
          "tradable": false
        }
      ],
      "relics": [
        {
          "tier": 0,
          "code": "A1",
          "refinement": 0,
          "quantity": 3
        }
      ],
      "foundry_states": [
        {
          "item_id": "wisp_prime",
          "name": "Wisp Prime",
          "owned": true,
          "mastered": false,
          "ready_to_build": true
        }
      ]
    }
  }'
```

Then query the derived views:

```bash
curl 'http://127.0.0.1:8010/api/client/v1/dashboard?user_hash=local-user'
curl 'http://127.0.0.1:8010/api/client/v1/foundry?user_hash=local-user'
curl 'http://127.0.0.1:8010/api/client/v1/inventory?user_hash=local-user&tradable_only=true'
curl 'http://127.0.0.1:8010/api/client/v1/relics?user_hash=local-user'
```

### 3. Launch the desktop shell

The desktop app reads the backend and displays the returned state in tabs.

```bash
uv run --package cachyframe-desktop cachyframe-desktop
```

By default it talks to `http://127.0.0.1:8010`. Override that with
`CACHYFRAME_DESKTOP__BACKEND_URL` if needed.

### 4. Decode or post capture events through the Proton helper

Decode the included fixture batch:

```bash
uv run --package cachyframe-proton-proxy cachyframe-proton-proxy \
  --fixture apps/proton-proxy/tests/fixtures/capture_batch.json
```

Decode the same fixture and post the normalized events to the backend:

```bash
uv run --package cachyframe-proton-proxy cachyframe-proton-proxy \
  --fixture apps/proton-proxy/tests/fixtures/capture_batch.json \
  --post-url http://127.0.0.1:8010 \
  --user-hash local-user
```

Generate Proton/Wine proxy instructions and local CA material:

```bash
uv run --package cachyframe-proton-proxy cachyframe-proton-proxy \
  --prefix ~/.steam/steam/steamapps/compatdata/230410/pfx
```

That command prints the environment variables to export before launching
Warframe in the same prefix and writes the CA under
`~/.local/share/cachyframe/ca/`.

### 5. Run worker jobs

The current worker entrypoint initializes storage, refreshes worldstate once,
prints a summary, and exits.

```bash
uv run --package cachyframe-worker cachyframe-worker
```

## Backend API Surface

Main project-native routes:

- `GET /healthz`
- `GET /api/client/v1/worldstate`
- `POST /api/client/v1/account/snapshots`
- `GET /api/client/v1/account/current`
- `POST /api/client/v1/capture-events:batch`
- `GET /api/client/v1/capture-events`
- `GET /api/client/v1/dashboard`
- `GET /api/client/v1/foundry`
- `GET /api/client/v1/inventory`
- `GET /api/client/v1/relics`
- `GET /api/client/v1/analytics/overview`
- `GET /api/client/v1/analytics/items/{item_id}`
- `POST /api/client/v1/public-links`
- `GET /api/client/v1/public-links`
- `DELETE /api/client/v1/public-links/{link_id}`
- `POST /api/client/v1/sniper/subscriptions`
- `GET /api/client/v1/sniper/subscriptions`
- `DELETE /api/client/v1/sniper/subscriptions/{subscription_id}`
- `POST /api/client/v1/diagnostics/upload`

AlecaFrame-compatible routes:

- `GET /api/stats/{user_hash}`
- `GET /api/stats/public`
- `GET /api/stats/public/getRelicInventory`

## Docker

A minimal Docker Compose file is included for the backend:

```bash
docker compose -f deploy/docker/docker-compose.yml up backend
```

It mounts the repo into a `python:3.12-slim` container, installs `uv`, syncs
the backend package, and starts the API on port `8010`.

## Tests

Run the current test suite with:

```bash
uv run pytest
```
