from __future__ import annotations

from typing import Any

import httpx

from .storage import LocalStore


class MetadataResolver:
    def __init__(self, store: LocalStore | None = None) -> None:
        self.store = store

    def _auth_headers(self, auth_ref: str | None) -> dict[str, str]:
        if not auth_ref or not self.store:
            return {}
        payload = self.store.load_json("auth", auth_ref, decrypt=True)
        if not payload:
            return {}
        header = payload.get("header", "Authorization")
        token = payload.get("token")
        scheme = payload.get("scheme", "Bearer")
        if not token:
            return {}
        return {header: f"{scheme} {token}"}

    def resolve(self, cluster_config: dict[str, Any]) -> dict[str, Any]:
        metadata = cluster_config.get("metadata", {})
        provider = metadata.get("provider", "static")

        if provider == "static":
            return cluster_config

        if provider == "http":
            endpoint = metadata.get("endpoint")
            if not endpoint:
                raise ValueError("metadata.endpoint is required for http provider")
            headers = self._auth_headers(metadata.get("auth_ref"))
            resp = httpx.get(endpoint, headers=headers, timeout=metadata.get("timeout_ms", 2000) / 1000)
            resp.raise_for_status()
            return resp.json()

        raise ValueError(f"unsupported metadata provider: {provider}")
