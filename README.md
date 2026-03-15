# LENS

Self-hosted LLM observability for local-first development.

## What It Includes

- `server/` FastAPI ingestion API, SQLite persistence, pricing engine, query APIs, and live WebSocket broadcasting
- `sdk/` Python SDK with sync/async transport plus OpenAI, Anthropic, and Gemini wrappers
- `dashboard/` React SPA for live traces, costs, failures, sessions, replay, and demo controls

## Quick Start

### Local development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ./server
pip install -e ./sdk[providers]
python -m lens_server
```

In another terminal:

```bash
cd dashboard
npm install
npm run dev
```

Open `http://localhost:4200`.

### Docker

```bash
docker-compose up --build
```

- API: `http://localhost:8100`
- Dashboard: `http://localhost:4200`

## Demo Flow

Seed the product with synthetic traces from either:

- the dashboard `Seed demo` button
- or the CLI script:

```bash
python scripts/demo_trace.py
```

## End-to-End Smoke Test

With the API running locally:

```bash
python scripts/e2e_smoke.py
```

This sends a trace through the SDK, verifies it lands in the API, and confirms session aggregation updates.

## Python SDK

Install the official Python package locally from this repo:

```bash
pip install ./sdk
```

Or with provider integrations:

```bash
pip install "./sdk[providers]"
```

See `sdk/README.md` for package usage details.

## Publishing

Python SDK release automation is documented in `docs/publishing.md`.

## API Surface

- `POST /api/v1/traces`
- `POST /api/v1/demo/trace`
- `GET /api/v1/traces`
- `GET /api/v1/traces/{trace_id}`
- `GET /api/v1/sessions`
- `GET /api/v1/sessions/{session_id}`
- `GET /api/v1/stats/overview`
- `GET /api/v1/stats/costs`
- `GET /api/v1/stats/failures`
- `GET /api/v1/health`
- `GET /ws/traces`

## Current MVP Status

- backend ingest/query/live stream is working
- Python SDK core and provider wrappers are working
- dashboard live feed, costs, failures, sessions, and demo flow are working
- Docker now runs both API and dashboard
- end-to-end smoke coverage exists for SDK to API flow
