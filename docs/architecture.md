# Architecture

## Current implementation

The repository is bootstrapped as a `uv` workspace with:

- shared domain models in `packages/core`
- persistence and repository APIs in `packages/storage`
- upstream clients in `packages/data-sources`
- local collector scaffolding in `packages/collectors`
- reusable Qt widgets in `packages/ui`
- application entrypoints in `apps/*`

## Capture model

- Exact inventory parity is modeled as Proton-side TLS capture.
- `EE.log` and OCR remain separate subsystems for overlays, trade correlation, and resilience.
- The current code includes certificate generation, Proton launch environment rendering,
  decoder registry scaffolding, and a `mitmproxy` addon placeholder.

## API model

The backend exposes:

- AlecaFrame-compatible read endpoints under `/api/stats/*`
- project-native write and management endpoints under `/api/client/v1/*`

