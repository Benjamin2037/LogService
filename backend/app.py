from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import Body, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from .cluster_config import ConfigValidationError, load_cluster_config
from .config import load_settings
from .loki_adapter import LokiAdapter, build_logql
from .metadata import MetadataResolver
from .code_search import search_code
from .models import (
    CodeSearchRequest,
    CodeSearchResponse,
    ExportRequest,
    ExportResponse,
    LogLineModel,
    QueryRequest,
    QueryResponse,
    AgentRunRequest,
    SkillCreateRequest,
    SkillExtractRequest,
)
from .rate_limit import TokenBucketLimiter
from .redaction import Redactor
from .skills import SkillManager
from .storage import LocalStore, StorageError

settings = load_settings()
store = LocalStore(settings.data_dir)
limiter = TokenBucketLimiter(rate_per_sec=1 / settings.min_interval_seconds, burst=1)
resolver = MetadataResolver(store)
skill_manager = SkillManager(store)
schema_path = Path(__file__).resolve().parents[1] / "config/schema/cluster_config.schema.json"
frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
redaction_path = settings.redaction_path or (settings.data_dir / "redaction.json")
redactor = Redactor.from_file(redaction_path)

app = FastAPI(title="LogService", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


if frontend_dir.exists():
    app.mount("/ui", StaticFiles(directory=frontend_dir, html=True), name="ui")


def _load_config(config_path: str | None) -> dict[str, Any]:
    path = Path(config_path) if config_path else settings.config_path
    if not path:
        raise HTTPException(status_code=400, detail="cluster_config_path is required")
    try:
        return load_cluster_config(path, schema_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConfigValidationError as exc:
        raise HTTPException(status_code=400, detail={"errors": exc.errors}) from exc


def _build_loki_adapter(cluster_config: dict[str, Any]) -> LokiAdapter:
    loki_cfg = cluster_config.get("loki", {})
    headers = dict(loki_cfg.get("headers", {}))
    auth = loki_cfg.get("auth", {})
    if auth.get("type") == "token":
        ref = auth.get("token_ref")
        if ref:
            try:
                payload = store.load_json("auth", ref, decrypt=True) or {}
            except StorageError as exc:
                raise HTTPException(status_code=401, detail=str(exc)) from exc
            token = payload.get("token")
            header = payload.get("header", "Authorization")
            scheme = payload.get("scheme", "Bearer")
            if token:
                headers[header] = f"{scheme} {token}"

    direction = loki_cfg.get("query_params", {}).get("direction", "backward")
    return LokiAdapter(
        base_url=loki_cfg.get("base_url", ""),
        tenant_header=loki_cfg.get("tenant_header"),
        tenant=loki_cfg.get("tenant"),
        headers=headers,
        direction=direction,
    )


@app.post("/api/query", response_model=QueryResponse)
def query_logs(payload: QueryRequest) -> QueryResponse:
    allowed, retry_after = limiter.allow(payload.cluster_id)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="rate limited",
            headers={"Retry-After": str(int(retry_after) + 1)},
        )

    cluster_config = _load_config(payload.cluster_config_path)
    cluster_config = resolver.resolve(cluster_config)

    if not cluster_config.get("loki", {}).get("base_url"):
        raise HTTPException(status_code=400, detail="loki.base_url is required")

    labels_cfg = cluster_config.get("labels", {})
    component_label = labels_cfg.get("component")
    cluster_label = labels_cfg.get("cluster")
    if not component_label or not cluster_label:
        raise HTTPException(status_code=400, detail="labels.cluster and labels.component are required")

    components = payload.components or cluster_config.get("components", [])
    if not components:
        raise HTTPException(status_code=400, detail="components is required")

    adapter = _build_loki_adapter(cluster_config)
    lines: list[LogLineModel] = []
    try:
        for component in components:
            labels = {cluster_label: payload.cluster_id, component_label: component}
            logql = build_logql(labels, payload.keywords)
            batch = adapter.query_with_slicing(
                logql=logql,
                start=payload.time_range.start,
                end=payload.time_range.end,
                limit=payload.max_lines - len(lines),
                window_seconds=payload.window_seconds,
            )
            lines.extend(LogLineModel(ts=item.ts, line=item.line, labels=item.labels) for item in batch)
            if len(lines) >= payload.max_lines:
                break
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if settings.redact_enabled:
        lines = [
            LogLineModel(ts=item.ts, line=redactor.redact_text(item.line), labels=item.labels)
            for item in lines
        ]

    return QueryResponse(lines=lines, truncated=len(lines) >= payload.max_lines)


@app.post("/api/export", response_model=ExportResponse)
def export_logs(payload: ExportRequest) -> ExportResponse:
    export_dir = settings.data_dir / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    path = export_dir / f"logservice_export_{timestamp}.{payload.format}"

    export_lines = payload.lines
    if settings.redact_enabled:
        export_lines = [
            LogLineModel(ts=line.ts, line=redactor.redact_text(line.line), labels=line.labels)
            for line in payload.lines
        ]

    if payload.format == "json":
        content = [line.model_dump() for line in export_lines]
        path.write_text(
            __import__("json").dumps(content, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    elif payload.format == "markdown":
        body = "\n".join(f\"{line.ts} {line.line}\" for line in export_lines)
        path.write_text(f\"```\\n{body}\\n```\\n\", encoding=\"utf-8\")
    else:
        body = "\n".join(f\"{line.ts} {line.line}\" for line in export_lines)
        path.write_text(body, encoding=\"utf-8\")

    return ExportResponse(path=str(path))


@app.get("/api/context/{session_id}")
def load_context(session_id: str) -> dict[str, Any]:
    data = store.load_json("context", session_id, decrypt=False)
    if data is None:
        raise HTTPException(status_code=404, detail="context not found")
    return data


@app.post("/api/context/{session_id}")
def save_context(session_id: str, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    store.save_json("context", session_id, payload, encrypt=False)
    return {"status": "ok"}


@app.get("/api/skills")
def list_skills() -> list[dict[str, Any]]:
    return skill_manager.list()


@app.post("/api/skills")
def create_skill(payload: SkillCreateRequest) -> dict[str, Any]:
    return skill_manager.create(payload.name, payload.triggers, payload.prompt_template)


@app.post("/api/skills/extract")
def extract_skill(payload: SkillExtractRequest) -> dict[str, Any]:
    return skill_manager.extract(payload.name, payload.keywords, payload.analysis_notes)


@app.post("/api/agent/run")
def run_agent(payload: AgentRunRequest) -> dict[str, Any]:
    job_id = f"job-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    job = {
        "id": job_id,
        "status": "queued",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "name": payload.name,
        "steps": payload.steps,
        "payload": payload.payload,
    }
    store.save_json("context", job_id, job, encrypt=False)
    return job


@app.get("/api/agent/{job_id}")
def get_agent_job(job_id: str) -> dict[str, Any]:
    job = store.load_json("context", job_id, decrypt=False)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.post("/api/code/search", response_model=CodeSearchResponse)
def code_search_endpoint(payload: CodeSearchRequest) -> CodeSearchResponse:
    try:
        hits = search_code(
            payload.path,
            payload.keywords,
            payload.max_hits,
            cache_root=settings.data_dir / "cache",
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CodeSearchResponse(hits=hits)
