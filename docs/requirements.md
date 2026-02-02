# LogService Requirements

## Purpose
Provide a Loki-based log capture and analysis service for TiDB Cloud components that enables users to enter simple keywords and time ranges to retrieve and analyze logs quickly, with strict limits to protect clusters.

## Goals
- Fast, keyword-first log discovery for TiDB Cloud components.
- Chat-style web UI with persistent local session/auth state.
- Safe and throttled access to Loki (max 100 log lines per response).
- Prompt skill library for reusable analysis patterns.
- Agent integration for multi-step log collection and analysis.
- Code path correlation for deeper investigations.
- Durable context saved to disk and recoverable across sessions.

## Users
- SRE/On-call: rapid triage and timeline reconstruction.
- Developer: root cause analysis with code correlation.
- Support/Incident manager: structured outputs and auditability.

## In Scope
1) Cluster discovery and metadata resolution
- Extract monitoring/log links from user input.
- Resolve authentication requirements (tenant headers, tokens).
- Resolve component labels (tidb, pd, tikv, tiflash, tiflow, ticdc).

2) Query input
- Keyword(s), time range, component(s), cluster ID.
- Relative and absolute time formats.

3) Log retrieval
- Hard cap of 100 lines per response.
- Rate limiting, backoff, and cooldown to protect clusters.

4) Web chat UX
- Conversational interface for queries and follow-ups.
- Local persistence of auth/session state.

5) Skill library
- Save/reuse user prompts as skills.
- Auto-extract reusable prompts from analysis sessions.

6) Agent integration
- Orchestrate multi-step workflows (collect multiple windows first, then analyze).

7) Code correlation
- Accept local code path and link logs to relevant files/lines.

8) Output formatting
- Summaries, sorted/grouped logs, export (text/JSON/Markdown).

9) Persistence and recovery
- Save full analysis context to disk; restore on next run.

## Out of Scope (Phase 1)
- Centralized log storage (Loki remains source of truth).
- High-volume export or continuous streaming.
- Full incident management (paging/tickets).
- Non-Loki backends.

## Non-Functional Requirements
- Performance: typical 15m query returns within 3s; larger ranges are staged.
- Reliability: graceful degradation when Loki is slow/unavailable.
- Security: least privilege; secrets redaction; encrypted local storage.
- Privacy: local-only storage by default.
- Observability: metrics for query counts, throttling, errors.

## Constraints
- Max 100 log lines per response.
- Avoid frequent queries that can impact cluster performance.
- Must support TiDB Cloud component label mapping.

## Assumptions
- Loki is reachable from the local environment or via proxy.
- Users possess valid credentials.
- Local disk is available for context storage.

## Acceptance Criteria
- Provide a detailed design document with module breakdown.
- Provide functional and implementation test plans.
- Provide Mac (web or client) installation instructions.
