import os
from pathlib import Path
from pydantic import BaseModel, Field


class Settings(BaseModel):
    env: str = Field(default="local")
    config_path: Path | None = None
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".logservice")
    max_lines: int = Field(default=100)
    min_interval_seconds: int = Field(default=10)
    redact_enabled: bool = Field(default=True)
    redaction_path: Path | None = None


def load_settings() -> Settings:
    env = os.getenv("LOGSERVICE_ENV", "local")
    config_path = os.getenv("LOGSERVICE_CONFIG")
    data_dir = os.getenv("LOGSERVICE_DATA_DIR")
    redact_enabled = os.getenv("LOGSERVICE_REDACT", "true").lower() in {"1", "true", "yes"}
    redaction_path = os.getenv("LOGSERVICE_REDACTION_PATH")
    values = {
        "env": env,
        "config_path": Path(config_path) if config_path else None,
        "redact_enabled": redact_enabled,
    }
    if data_dir:
        values["data_dir"] = Path(data_dir)
    if redaction_path:
        values["redaction_path"] = Path(redaction_path)
    return Settings(**values)
