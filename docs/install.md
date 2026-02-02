# LogService Installation (macOS)

## Option A: Web (Local) Deployment

### Prerequisites
- macOS 13+
- Python 3.11+
- Node.js 20+

### Steps
1) Create a virtual environment and install backend dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

2) Set security-related environment variables
```bash
export LOGSERVICE_CONFIG=/path/to/cluster.json
export LOGSERVICE_MASTER_KEY=$(python - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
)
```

3) Install frontend dependencies
```bash
cd frontend
npm install
```

4) Run backend API (bind to localhost only)
```bash
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

5) Run frontend dev server
```bash
cd frontend
npm run dev
```

6) Open the UI
- Visit `http://localhost:8000/` (or the frontend dev URL).

## Security Notes
- Keep the API bound to `127.0.0.1` unless a secure reverse proxy is in place.
- Store tokens only via `LOGSERVICE_MASTER_KEY` encrypted storage.
- Redact secrets in exports; avoid sharing raw logs externally.

## Option B: Local Desktop Wrapper (Future)
- Package the web UI + API into a single macOS app (e.g., Tauri/Electron).
- Reuse the same backend service and local storage.

## First-Run Setup
- Configure cluster metadata and Loki auth.
- Store credentials locally (encrypted).
- Confirm label mappings for TiDB components.
