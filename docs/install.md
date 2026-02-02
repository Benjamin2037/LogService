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

2) Install frontend dependencies
```bash
cd frontend
npm install
```

3) Run backend API
```bash
uvicorn backend.app:app --reload --port 8000
```

4) Run frontend dev server
```bash
cd frontend
npm run dev
```

5) Open the UI
- Visit `http://localhost:8000/` (or the frontend dev URL).

## Option B: Local Desktop Wrapper (Future)
- Package the web UI + API into a single macOS app (e.g., Tauri/Electron).
- Reuse the same backend service and local storage.

## First-Run Setup
- Configure cluster metadata and Loki auth.
- Store credentials locally (encrypted).
- Confirm label mappings for TiDB components.

