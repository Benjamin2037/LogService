from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .storage import LocalStore


def _slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip())
    return value.strip("-").lower() or "skill"


class SkillManager:
    def __init__(self, store: LocalStore) -> None:
        self.store = store

    def list(self) -> list[dict[str, Any]]:
        skills_dir = self.store.root / "skills"
        skills: list[dict[str, Any]] = []
        for path in skills_dir.glob("*.json"):
            data = self.store.load_json("skills", path.stem, decrypt=False)
            if data:
                skills.append(data)
        return skills

    def create(self, name: str, triggers: list[str], prompt_template: str) -> dict[str, Any]:
        created_at = datetime.now(timezone.utc).isoformat()
        skill_id = f"{_slugify(name)}-{int(datetime.now().timestamp())}"
        payload = {
            "id": skill_id,
            "name": name,
            "triggers": triggers,
            "prompt_template": prompt_template,
            "version": 1,
            "created_at": created_at,
        }
        self.store.save_json("skills", skill_id, payload, encrypt=False)
        return payload

    def extract(self, name: str, keywords: list[str], analysis_notes: str) -> dict[str, Any]:
        template = analysis_notes.strip()
        if len(template) > 2000:
            template = template[:2000] + "..."
        return self.create(name=name, triggers=keywords, prompt_template=template)
