# LogService Design

## 1. Overview
LogService is a local-first Loki log capture and analysis service for TiDB Cloud components. It provides a chat-style web UI, strict log limits (<= 100 lines per response), and persistent local context to enable fast, repeatable investigations without overloading clusters.

## 2. Architecture

### 2.1 High-Level Components
- **Web UI (Chat)**: conversational search, timeline, skill management, exports.
- **API Service**: request orchestration, throttling, session/auth storage, policy enforcement.
- **Metadata Resolver**: cluster/tenant/label resolution for TiDB components.
- **Loki Adapter**: LogQL builder, query slicing, paging, sampling, limit enforcement.
- **Skill Manager**: prompt templates, auto-extraction, versioning.
- **Agent Orchestrator**: multi-step workflows (collect then analyze).
- **Code Correlator**: local code search/indexing to link log lines to files.
- **Context Store**: durable analysis context and session history on disk.

### 2.2 Runtime Flow (Text Diagram)
```
User -> Web UI -> API Service
API Service -> (Metadata Resolver -> Loki Adapter) -> Logs
API Service -> Skill Manager -> Prompt Templates
API Service -> Agent Orchestrator -> Multi-step Tasks
API Service -> Code Correlator -> Code Matches
API Service -> Context Store -> Persist/Restore
```

## 3. Data Model

### 3.1 Cluster Config
```json
{
  "cluster_id": "us-east-1-f02",
  "display_name": "prod-us-east",
  "loki": {
    "base_url": "https://loki.example.com",
    "tenant_header": "X-Scope-OrgID",
    "tenant": "tidb-cloud",
    "auth_type": "token",
    "token_ref": "keychain:logservice/loki"
  },
  "labels": {
    "cluster": "cluster",
    "namespace": "namespace",
    "pod": "pod",
    "component": "component"
  },
  "components": ["tidb", "pd", "tikv", "tiflash", "tiflow", "ticdc"]
}
```

### 3.2 Query Request
```json
{
  "cluster_id": "us-east-1-f02",
  "components": ["pd"],
  "keywords": ["leader", "ready"],
  "time_range": {"from": "2026-02-02T08:00:00Z", "to": "2026-02-02T08:15:00Z"},
  "max_lines": 100,
  "mode": "chat",
  "skill_id": "pd-leader-ready"
}
```

### 3.3 Log Line
```json
{
  "ts": "2026-02-02T08:02:11.123Z",
  "component": "pd",
  "pod": "pd-0",
  "level": "info",
  "message": "...",
  "labels": {"cluster": "us-east-1-f02", "namespace": "tidb"}
}
```

### 3.4 Skill Template
```json
{
  "id": "pd-leader-ready",
  "name": "PD leader/ready slowdown",
  "triggers": ["leader", "ready"],
  "prompt_template": "Analyze PD leader election and ready delay...",
  "created_at": "2026-02-02T09:00:00Z",
  "version": 3
}
```

### 3.5 Analysis Context
```json
{
  "session_id": "s-20260202-001",
  "cluster_id": "us-east-1-f02",
  "queries": [ ... ],
  "log_samples": [ ... ],
  "analysis_notes": "...",
  "skills_used": ["pd-leader-ready"],
  "code_refs": ["/path/to/repo/pd/server/..."]
}
```

## 4. API Design

### 4.1 Session & Auth
- `POST /api/session` : create/load session
- `POST /api/auth/store` : store auth (encrypted)
- `GET /api/auth/status` : auth availability

### 4.2 Query & Logs
- `POST /api/query` : keyword/time query
- `GET /api/query/{id}` : query status/result
- `POST /api/export` : export results (text/json/md)

### 4.3 Skills
- `GET /api/skills` : list skills
- `POST /api/skills` : create skill
- `POST /api/skills/extract` : extract skill from analysis

### 4.4 Agent
- `POST /api/agent/run` : run multi-step job
- `GET /api/agent/{id}` : job status/result

### 4.5 Code Correlation
- `POST /api/code/index` : index a code path
- `POST /api/code/search` : search logs -> code hits

### 4.6 Context
- `GET /api/context/{session_id}` : load context
- `POST /api/context/{session_id}` : save context

## 5. Query Planning & Throttling

### 5.1 LogQL Builder
- Build label selectors from cluster/component mappings.
- Inject keyword filters with safe escaping.
- Split large time ranges into windows (e.g., 5m slices).

### 5.2 Hard Limits
- Enforce `max_lines <= 100` at API boundary.
- Apply sampling if raw results exceed limit (latest-first + spread).

### 5.3 Rate Limiting
- Token bucket per (cluster_id, user_id) with default 1 req / 10s.
- Global cap across all users to protect shared resources.
- Exponential backoff on Loki errors or overload signals.

### 5.4 Cooldown Feedback
- UI receives remaining cooldown time and suggested next query time.

## 6. Skill Extraction Pipeline
1) Capture final analysis and associated keywords.
2) Extract triggers (keywords, component, context tags).
3) Generate prompt template and metadata.
4) Store versioned skill and link to session.

## 7. Agent Orchestration
- A job is a DAG of steps: collect -> normalize -> analyze -> summarize.
- Collect step fetches multiple time windows (configurable) before analysis.
- Analysis step can call user-provided model with structured input.

## 8. Code Correlation
- Accept a local path; index using ripgrep or lightweight AST parsing.
- Map log keywords to file/line hits; show snippets in UI.
- Cache index per repo path with hash of file list.

## 9. Local Persistence

### 9.1 Storage Layout
```
~/.logservice/
  auth/ (encrypted tokens)
  sessions/
  skills/
  context/
  cache/
```

### 9.2 Encryption
- Use OS keychain where available; fallback to AES-GCM with user passphrase.
- Redact tokens in UI and exports by default.

## 10. UI/UX Details
- Chat input with structured fields (cluster, component, time range, keyword).
- Timeline view with event markers and component filters.
- Log viewer with highlight, copy, and export actions.
- Skill manager: list, preview, apply, edit.
- Agent panel: progress, steps, partial results.

## 11. Integration Framework
- Config schema: `config/schema/cluster_config.schema.json`
- Example config: `config/examples/cluster.example.json`
- Input worksheet: `docs/metadata_auth_inputs.md`
- Purpose: capture Loki auth, label mapping, metadata provider, and network topology inputs.

## 12. Observability
- Metrics: query count, throttled count, avg latency, Loki errors.
- Local logs for debugging (no secret output).

## 13. Failure Handling
- Loki unavailable: return clear message and retry window.
- Invalid auth: prompt re-auth and clear stored token.
- Large time range: auto-split and partial results with warning.
