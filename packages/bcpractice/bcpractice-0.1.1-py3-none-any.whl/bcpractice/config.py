"""Configuration management for API keys and settings."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Literal

CONFIG_DIR = Path.home() / ".bcpractice"
CONFIG_FILE = CONFIG_DIR / "config.json"

Provider = Literal["openai", "anthropic"]


@dataclass
class Config:
    provider: Provider | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    default_length: str = "medium"  # quick, medium, full

    def get_api_key(self) -> str | None:
        """Get the API key for the configured provider."""
        if self.provider == "openai":
            return self.openai_api_key or os.environ.get("OPENAI_API_KEY")
        elif self.provider == "anthropic":
            return self.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        return None

    def is_configured(self) -> bool:
        """Check if the config has a valid provider and API key."""
        return self.provider is not None and self.get_api_key() is not None


def load_config() -> Config:
    """Load configuration from file or return defaults."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                data = json.load(f)
                return Config(**data)
        except (json.JSONDecodeError, TypeError):
            return Config()
    return Config()


def save_config(config: Config) -> None:
    """Save configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(asdict(config), f, indent=2)
    # Secure the config file (owner read/write only)
    os.chmod(CONFIG_FILE, 0o600)


def clear_config() -> None:
    """Remove the configuration file."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()


# Length presets: (min_problems, max_problems)
LENGTH_PRESETS = {
    "quick": (5, 8),
    "medium": (12, 15),
    "full": (20, 25),
}


def get_problem_count(length: str) -> int:
    """Get the target problem count for a length preset."""
    min_count, max_count = LENGTH_PRESETS.get(length, LENGTH_PRESETS["medium"])
    # Return the midpoint
    return (min_count + max_count) // 2
