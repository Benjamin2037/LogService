import json
import os
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken


class StorageError(RuntimeError):
    pass


class LocalStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        for name in ("auth", "sessions", "skills", "context", "cache"):
            (self.root / name).mkdir(parents=True, exist_ok=True)

    def _fernet(self) -> Fernet:
        key = os.getenv("LOGSERVICE_MASTER_KEY")
        if not key:
            raise StorageError("LOGSERVICE_MASTER_KEY is required for encrypted storage")
        return Fernet(key.encode("utf-8"))

    def save_json(self, category: str, name: str, data: dict[str, Any], *, encrypt: bool) -> Path:
        category_dir = self.root / category
        category_dir.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

        if encrypt:
            token = self._fernet().encrypt(payload)
            path = category_dir / f"{name}.bin"
            path.write_bytes(token)
            return path

        path = category_dir / f"{name}.json"
        path.write_bytes(payload)
        return path

    def load_json(self, category: str, name: str, *, decrypt: bool) -> dict[str, Any] | None:
        category_dir = self.root / category
        if decrypt:
            path = category_dir / f"{name}.bin"
            if not path.exists():
                return None
            try:
                data = self._fernet().decrypt(path.read_bytes())
            except InvalidToken as exc:
                raise StorageError("Encrypted payload cannot be decrypted") from exc
            return json.loads(data.decode("utf-8"))

        path = category_dir / f"{name}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
