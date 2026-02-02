# LogService User Guide

This guide explains how to use LogService features end-to-end.

## 1) Quick Start

### Backend
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### Environment
```bash
export LOGSERVICE_CONFIG=/path/to/cluster.json
export LOGSERVICE_MASTER_KEY=$(python - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
)
```

### Run API
```bash
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

### Open UI
- Visit `http://localhost:8000/ui`

### macOS Client
```bash
cd client-mac
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## 2) Configure Loki & Metadata

### Cluster Config
- Edit a config file based on `config/examples/cluster.example.json`.
- Validate with the schema `config/schema/cluster_config.schema.json`.

### Metadata Provider
- `static`: use local config only.
- `http`: set `metadata.endpoint` + `metadata.auth_ref`.

### Auth Storage
- Store token payloads using encrypted local storage (category `auth`).
- Example payload:
```json
{
  "header": "Authorization",
  "scheme": "Bearer",
  "token": "<token>"
}
```

## 3) Interaction Modes

### Timeline (default)
1) Click an event marker or pick a time preset.
2) Review the generated time window.
3) Add minimal keywords and run the query.

### Guided
1) Fill steps (Target → Scope → Keywords → Time Range).
2) Run query.

### Hybrid
1) Pick a timeline window first.
2) Refine with guided fields.
3) Run query.

## 4) Query Logs

### Inputs
- Cluster ID
- Components
- Keywords
- Time range

### Constraints
- Max 100 log lines per response.
- Cooldown enforced to protect cluster.

### Result
- Logs are shown in the Conversation pane.
- If results exceed 100 lines, they are truncated.

## 5) Export Logs

1) Run a query to populate results.
2) Click Export Text.
3) Export file saved under `~/.logservice/exports/`.

Supported formats: `text`, `json`, `markdown`.

## 6) Skills

### Create
- Use `/api/skills` to create a prompt skill.

### Extract
- Use `/api/skills/extract` with analysis notes to auto-generate a skill.

### Apply
- Use skill prompts to guide analysis.

## 7) Agent (Multi-step)

### Run
- Use `/api/agent/run` with step definitions.

### Check Status
- Use `/api/agent/{id}`.

## 8) Code Search

### Local Path
- Use `/api/code/search` with `path=/path/to/repo` and keywords.

### GitHub URL
- Use `path=https://github.com/org/repo`.
- Repo will be cloned to `~/.logservice/cache/repos` on first use.

## 9) Context

### Save
- `POST /api/context/{session_id}`

### Load
- `GET /api/context/{session_id}`

## 10) Security Notes
- Keep backend bound to `127.0.0.1`.
- Store secrets only via encrypted local storage.
- Avoid exporting raw logs with sensitive data.
