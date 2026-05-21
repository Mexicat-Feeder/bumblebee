# Bumblebee Dashboard

A monitoring and management UI for Bumblebee projects. Provides real-time visibility
into ticket queues, gate progress, loop health, hardware metrics, and AI model activity.

## Structure

```
dashboard/
├── api/          Python/FastAPI backend
├── ui/           SvelteKit frontend source
└── dashboard.config.example.json   Config template
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- A Bumblebee `tickets.db` (produced by the engine)

## Setup

### 1. Install dependencies

```bash
# Backend
pip install -r api/requirements.txt

# Frontend
cd ui && npm install
```

### 2. Configure

Copy the example config and edit it to point at your project database(s):

```bash
cp dashboard.config.example.json dashboard.config.json
```

Edit `dashboard.config.json`:

```json
{
  "ticketDbPaths": {
    "my-project": "/absolute/path/to/projects/my-project/tickets.db"
  },
  "apiPort": 8765,
  "healthChecks": []
}
```

### 3. Optional environment variables

| Variable | Purpose | Default |
|---|---|---|
| `DASHBOARD_CONFIG` | Path to config file | `dashboard.config.json` |
| `OPENCLAW_CONFIG` | Path to `openclaw.json` for gateway features | `~/.openclaw/openclaw.json` |
| `OPENCLAW_SESSIONS_PATH` | Path to OpenClaw `sessions.json` for Pixel stats | *(empty — panel shows unavailable)* |
| `RESEARCH_SIFT_DIR` | Directory where research reports are written | `<research_root>/Sift` |

## Running

### Quick start (recommended)

From the `dashboard/` directory:

```powershell
.\start.ps1
```

This will install deps, build the frontend (if needed), and start the server on port 8765.
Pass `-Port 9000` to use a different port.

### Development

Start the API server:

```bash
# From the dashboard/ directory
python -m uvicorn api.main:app --port 8765 --reload
```

Start the UI dev server (in a separate terminal):

```bash
cd ui
npm run dev
```

The UI dev server proxies `/api` calls to `http://localhost:8765` automatically.

### Production

Build the UI:

```bash
cd ui
npm run build
```

This outputs static files to `ui/build/`. The API serves them directly — no symlinks needed.

Then run the server:

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8765
```

Open `http://localhost:8765` in your browser.

## Notes

- The `RESEARCH_SIFT_DIR` / research DB features are only relevant if you use the old-swarm
  research queue. They degrade gracefully when not configured.
- Gateway/Telegram features require an active OpenClaw installation with `openclaw.json`.
  If the file isn't present, those endpoints return empty data without crashing.
