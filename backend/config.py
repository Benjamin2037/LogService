import os
from pathlib import Path
from pydantic import BaseModel, Field


class Settings(BaseModel):
    env: str = Field(default="local")
    config_path: Path | None = None
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".logservice")
    max_lines: int = Field(default=100)
    min_interval_seconds: int = Field(default=10)


def load_settings() -> Settings:
    env = os.getenv("LOGSERVICE_ENV", "local")
    config_path = os.getenv("LOGSERVICE_CONFIG")
    data_dir = os.getenv("LOGSERVICE_DATA_DIR")
    values = {
        "env": env,
        "config_path": Path(config_path) if config_path else None,
    }
    if data_dir:
        values["data_dir"] = Path(data_dir)
    return Settings(**values)
