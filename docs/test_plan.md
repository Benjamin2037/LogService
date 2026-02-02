# LogService Test Plan

## 1. Test Scope
- Functional validation of log retrieval, UI workflow, skill library, agent orchestration, and persistence.
- Implementation tests for core modules and API contracts.
- Performance and safety constraints (rate limiting, max 100 lines).

## 2. Test Environments
- Local Mac (Web UI + API service).
- Mock Loki backend (deterministic responses).
- Optional: Staging Loki with limited access for integration.

## 3. Test Data
- Sample Loki responses for each component.
- Synthetic logs covering keyword matches, multi-component, and large volume.
- Redaction samples (tokens, secrets).

## 4. Functional Test Cases

### 4.1 Auth & Session
- Store token securely; reload session and re-use auth.
- Invalid token -> error message + re-auth prompt.

### 4.2 Metadata & Labels
- Resolve cluster URL -> correct tenant/header/labels.
- Component mapping for tidb/pd/tikv/tiflash/tiflow/ticdc.

### 4.3 Query Input
- Relative time (last 15m) and absolute time ranges.
- Multi-keyword queries; keyword escaping.

### 4.4 Log Retrieval
- Enforce max 100 lines even when Loki returns more.
- Throttling: second request within cooldown is rejected or delayed.
- Window slicing for large time range.

### 4.5 Chat UI
- End-to-end query from chat input to results display.
- Highlight keywords; copy/export logs.

### 4.6 Skill Library
- Create, edit, and apply skill.
- Auto-extract skill after analysis.

### 4.7 Agent Orchestration
- Multi-window collection then analysis.
- Step failures are reported with partial results.

### 4.8 Code Correlation
- Index path; map keywords to files.
- Changes in repo invalidate cache.

### 4.9 Persistence & Recovery
- Save context to disk; restart app and resume session.

### 4.10 Security & Redaction
- Secret patterns are masked in UI and exports.

## 5. Implementation Test Plan

### 5.1 Unit Tests
- LogQL builder: label selectors, keyword escaping.
- Rate limiter: token bucket behavior and cooldown.
- Skill extraction: trigger detection and template generation.
- Context store: read/write, encryption/decryption.

### 5.2 Integration Tests
- API + Mock Loki for query and limit enforcement.
- API + Skill manager + context store end-to-end.

### 5.3 E2E Tests
- Web UI flow: query -> results -> export.
- Agent flow: create job -> progress -> final summary.

### 5.4 Performance Tests
- Baseline latency for 15m query under mock backend.
- High-volume query with enforced limits.

### 5.5 Failure Injection
- Loki timeout -> retry/backoff behavior.
- Invalid auth -> re-auth path.

## 6. Exit Criteria
- All functional tests pass.
- All unit/integration tests pass.
- Performance and throttling constraints met.
- No unmasked secrets in outputs.
