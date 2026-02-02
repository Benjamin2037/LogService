from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx


@dataclass
class LogLine:
    ts: str
    line: str
    labels: dict[str, str]


def _escape_keyword(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_logql(labels: dict[str, str], keywords: list[str]) -> str:
    selector = ",".join(f'{k}="{v}"' for k, v in labels.items())
    query = f"{{{selector}}}"
    for kw in keywords:
        if kw:
            query += f' |= "{_escape_keyword(kw)}"'
    return query


def _to_nanos(ts: datetime) -> int:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return int(ts.timestamp() * 1_000_000_000)


class LokiAdapter:
    def __init__(
        self,
        base_url: str,
        tenant_header: str | None = None,
        tenant: str | None = None,
        headers: dict[str, str] | None = None,
        timeout_seconds: int = 10,
        direction: str = "backward",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.tenant_header = tenant_header
        self.tenant = tenant
        self.headers = headers or {}
        self.timeout_seconds = timeout_seconds
        self.direction = direction

    def _headers(self) -> dict[str, str]:
        headers = dict(self.headers)
        if self.tenant_header and self.tenant:
            headers[self.tenant_header] = self.tenant
        return headers

    def query_range(
        self,
        logql: str,
        start: datetime,
        end: datetime,
        limit: int,
    ) -> list[LogLine]:
        params = {
            "query": logql,
            "start": _to_nanos(start),
            "end": _to_nanos(end),
            "limit": limit,
            "direction": self.direction,
        }
        url = f"{self.base_url}/loki/api/v1/query_range"
        resp = httpx.get(url, params=params, headers=self._headers(), timeout=self.timeout_seconds)
        resp.raise_for_status()
        payload = resp.json()
        result = payload.get("data", {}).get("result", [])

        lines: list[LogLine] = []
        for stream in result:
            labels = stream.get("stream", {})
            for ts, line in stream.get("values", []):
                lines.append(LogLine(ts=ts, line=line, labels=labels))
        return lines

    def query_with_slicing(
        self,
        logql: str,
        start: datetime,
        end: datetime,
        limit: int,
        window_seconds: int = 300,
    ) -> list[LogLine]:
        results: list[LogLine] = []
        if self.direction == "backward":
            cursor = end
            while cursor > start and len(results) < limit:
                window_start = max(start, cursor - timedelta(seconds=window_seconds))
                batch = self.query_range(logql, window_start, cursor, limit - len(results))
                results.extend(batch)
                cursor = window_start
        else:
            cursor = start
            while cursor < end and len(results) < limit:
                window_end = min(end, cursor + timedelta(seconds=window_seconds))
                batch = self.query_range(logql, cursor, window_end, limit - len(results))
                results.extend(batch)
                cursor = window_end
        return results[:limit]
