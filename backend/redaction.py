from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

DEFAULT_PATTERNS: list[tuple[str, str]] = [
    (r"(?i)(authorization|x[-_]?auth[-_]?token|token|api[-_]?key|secret|password)\s*[:=]\s*([A-Za-z0-9\-_.~+/=]+)", r"\1=***"),
    (r"(?i)bearer\s+[A-Za-z0-9\-_.~+/=]+", "Bearer ***"),
    (r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}", "***JWT***"),
    (r"AKIA[0-9A-Z]{16}", "***AWS_ACCESS_KEY***"),
    (r"(?i)aws_secret_access_key\s*[:=]\s*[A-Za-z0-9/+=]{20,}", "aws_secret_access_key=***"),
    (r"(?i)(password|passwd|pwd)\s*[:=]\s*\S+", r"\1=***"),
]


@dataclass
class Redactor:
    patterns: list[tuple[re.Pattern[str], str]]

    @classmethod
    def default(cls) -> "Redactor":
        compiled = [(re.compile(p), r) for p, r in DEFAULT_PATTERNS]
        return cls(compiled)

    @classmethod
    def from_file(cls, path: Path) -> "Redactor":
        if not path.exists():
            return cls.default()
        data = json.loads(path.read_text(encoding="utf-8"))
        patterns: list[tuple[re.Pattern[str], str]] = []
        for item in data.get("patterns", []):
            pattern = item.get("pattern")
            replace = item.get("replace", "***")
            if not pattern:
                continue
            flags = re.IGNORECASE if item.get("ignore_case", True) else 0
            patterns.append((re.compile(pattern, flags), replace))
        return cls(patterns or cls.default().patterns)

    def redact_text(self, text: str) -> str:
        redacted = text
        for regex, replace in self.patterns:
            redacted = regex.sub(replace, redacted)
        return redacted

    def redact_lines(self, lines: Iterable[str]) -> list[str]:
        return [self.redact_text(line) for line in lines]
