"""Configuration management for kalle."""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class ProviderConfig(BaseModel):
    base_url: str = "https://ollama.com/v1"
    api_key: str | None = Field(default_factory=lambda: os.getenv("KALLE_API_KEY"))
    fast_model: str = "deepseek-v4.1-flash:cloud"
    strong_model: str = "kimi-k2.6:cloud"
    temperature: float = 0.1


class Config(BaseModel):
    provider: ProviderConfig = Field(default_factory=ProviderConfig)


def _config_search_paths() -> list[Path]:
    return [
        Path("./kalle.yaml"),
        Path.home() / ".config" / "kalle" / "config.yaml",
    ]


def load_config(config_path: str | None = None) -> Config:
    """Load config from YAML file with env var overrides."""
    raw: dict = {}

    if config_path:
        path = Path(config_path)
        if path.exists():
            raw = yaml.safe_load(path.read_text()) or {}
    else:
        for path in _config_search_paths():
            if path.exists():
                raw = yaml.safe_load(path.read_text()) or {}
                break

    config = Config.model_validate(raw)

    # Env var overrides (always win over file)
    p = config.provider
    if val := os.getenv("KALLE_API_KEY"):
        p.api_key = val
    if val := os.getenv("KALLE_BASE_URL"):
        p.base_url = val
    if val := os.getenv("KALLE_FAST_MODEL"):
        p.fast_model = val
    if val := os.getenv("KALLE_STRONG_MODEL"):
        p.strong_model = val

    return config
