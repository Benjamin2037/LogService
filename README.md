# LogService

Local-first Loki log capture and analysis service for TiDB Cloud components (tidb, pd, tikv, tiflash, tiflow, ticdc).

## Highlights
- Keyword + time range log retrieval with strict 100-line cap.
- Chat-style web UX and persistent local context.
- Skill library for reusable analysis prompts.
- Agent-ready multi-step log collection and analysis.
- Code correlation for local repo paths.

## Documents
- Requirements: `docs/requirements.md`
- Design: `docs/design.md`
- Test plan: `docs/test_plan.md`
- Installation (macOS): `docs/install.md`
- Metadata/Auth framework: `docs/metadata_auth_framework.md`
- Metadata/Auth inputs: `docs/metadata_auth_inputs.md`
- Agent integration inputs: `docs/agent_integration_inputs.md`

## Config
- Schema: `config/schema/cluster_config.schema.json`
- Example: `config/examples/cluster.example.json`

## Quick Start (Local)

### 1) Backend
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 2) Environment
```bash
export LOGSERVICE_CONFIG=/path/to/cluster.json
export LOGSERVICE_MASTER_KEY=$(python - <<'PY'
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
)
```

### 3) Run API
```bash
uvicorn backend.app:app --reload --port 8000
```

### 4) Open UI
Visit `http://localhost:8000/ui`.

## Tests
```bash
pip install -r requirements-dev.txt
pytest
```

## Notes
- Loki is the source of truth; LogService does not ingest or store raw logs.
- Results are capped at 100 lines per response to protect clusters.
- The UI is served from `/ui` by the backend.
