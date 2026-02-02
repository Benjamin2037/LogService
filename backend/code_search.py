from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


@dataclass(frozen=True)
class GithubRepoRef:
    owner: str
    repo: str
    branch: str | None
    subpath: str | None


def _rg_available() -> bool:
    return shutil.which("rg") is not None


def _git_available() -> bool:
    return shutil.which("git") is not None


def _build_pattern(keywords: Iterable[str]) -> str:
    escaped = [re.escape(k) for k in keywords if k]
    return "|".join(escaped)


def _is_github_url(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return False
    return parsed.netloc in {"github.com", "www.github.com"}


def _parse_github_url(value: str) -> GithubRepoRef:
    parsed = urlparse(value)
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 2:
        raise ValueError("invalid GitHub URL")
    owner, repo = parts[0], parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]

    branch = None
    subpath = None
    if len(parts) >= 4 and parts[2] in {"tree", "blob"}:
        branch = parts[3]
        if len(parts) > 4:
            subpath = "/".join(parts[4:])

    return GithubRepoRef(owner=owner, repo=repo, branch=branch, subpath=subpath)


def _safe_repo_dir_name(ref: GithubRepoRef) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "-", f"{ref.owner}_{ref.repo}")


def _materialize_github_repo(ref: GithubRepoRef, cache_root: Path) -> Path:
    if not _git_available():
        raise RuntimeError("git is required for GitHub code search")

    repo_root = cache_root / "repos"
    repo_root.mkdir(parents=True, exist_ok=True)
    repo_dir = repo_root / _safe_repo_dir_name(ref)

    if repo_dir.exists():
        if not (repo_dir / ".git").exists():
            raise RuntimeError(f"cache path is not a git repo: {repo_dir}")
        return repo_dir

    clone_url = f"https://github.com/{ref.owner}/{ref.repo}.git"
    cmd = ["git", "clone", "--depth", "1"]
    if ref.branch:
        cmd += ["--branch", ref.branch]
    cmd += [clone_url, str(repo_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git clone failed")
    return repo_dir


def _search_local(path: Path, keywords: list[str], max_hits: int) -> list[dict[str, str | int]]:
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


def search_code(
    path: str | Path,
    keywords: list[str],
    max_hits: int,
    cache_root: Path | None = None,
) -> list[dict[str, str | int]]:
    if not keywords:
        return []

    path_value = str(path)
    if _is_github_url(path_value):
        ref = _parse_github_url(path_value)
        cache_root = cache_root or Path(os.path.expanduser("~/.logservice/cache"))
        repo_dir = _materialize_github_repo(ref, cache_root)
        target = repo_dir / ref.subpath if ref.subpath else repo_dir
        return _search_local(target, keywords, max_hits)

    return _search_local(Path(path_value), keywords, max_hits)
