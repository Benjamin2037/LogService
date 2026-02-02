from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterable


def _rg_available() -> bool:
    return shutil.which("rg") is not None


def _build_pattern(keywords: Iterable[str]) -> str:
    escaped = [re.escape(k) for k in keywords if k]
    return "|".join(escaped)


def search_code(path: Path, keywords: list[str], max_hits: int) -> list[dict[str, str | int]]:
    if not keywords:
        return []
    if not path.exists():
        raise FileNotFoundError(f"code path not found: {path}")

    pattern = _build_pattern(keywords)
    hits: list[dict[str, str | int]] = []

    if _rg_available():
        cmd = [
            "rg",
            "-n",
            "--no-heading",
            "--max-count",
            str(max_hits),
            pattern,
            str(path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.stdout:
            for line in result.stdout.splitlines():
                parts = line.split(":", 2)
                if len(parts) == 3:
                    file_path, line_no, text = parts
                    hits.append({"file": file_path, "line": int(line_no), "text": text})
        return hits[:max_hits]

    # Fallback: simple line scan
    for file_path in path.rglob("*"):
        if file_path.is_dir():
            continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for idx, line in enumerate(content, start=1):
            if any(k in line for k in keywords):
                hits.append({"file": str(file_path), "line": idx, "text": line})
                if len(hits) >= max_hits:
                    return hits

    return hits
