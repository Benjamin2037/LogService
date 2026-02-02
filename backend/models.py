from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TimeRange(BaseModel):
    start: datetime
    end: datetime


class QueryRequest(BaseModel):
    cluster_id: str
    cluster_config_path: str | None = None
    components: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    time_range: TimeRange
    max_lines: int = Field(default=100, ge=1, le=100)
    window_seconds: int = Field(default=300, ge=10, le=3600)


class LogLineModel(BaseModel):
    ts: str
    line: str
    labels: dict[str, str]


class QueryResponse(BaseModel):
    lines: list[LogLineModel]
    truncated: bool


class ExportRequest(BaseModel):
    format: Literal["text", "json", "markdown"] = "text"
    lines: list[LogLineModel]


class ExportResponse(BaseModel):
    path: str

class SkillCreateRequest(BaseModel):
    name: str
    triggers: list[str] = Field(default_factory=list)
    prompt_template: str


class SkillExtractRequest(BaseModel):
    name: str
    keywords: list[str] = Field(default_factory=list)
    analysis_notes: str


class SkillModel(BaseModel):
    id: str
    name: str
    triggers: list[str]
    prompt_template: str
    version: int
    created_at: datetime

class AgentRunRequest(BaseModel):
    name: str
    steps: list[dict] = Field(default_factory=list)
    payload: dict = Field(default_factory=dict)

class CodeSearchRequest(BaseModel):
    path: str
    keywords: list[str] = Field(default_factory=list)
    max_hits: int = Field(default=50, ge=1, le=500)


class CodeSearchHit(BaseModel):
    file: str
    line: int
    text: str


class CodeSearchResponse(BaseModel):
    hits: list[CodeSearchHit]
