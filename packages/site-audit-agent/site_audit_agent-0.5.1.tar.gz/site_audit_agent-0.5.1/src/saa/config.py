"""Configuration loading for SAA."""

import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv


@dataclass
class Config:
    """SAA configuration with hierarchical loading."""

    # Browser settings (empty = let Playwright auto-detect)
    chromium_path: str = ""
    headless: bool = True

    # Crawling settings
    pacing: str = "medium"  # off, low, medium, high
    max_pages: int = 50
    default_depth: int = 3

    # LLM settings
    default_llm: str = "xai:grok-4"
    xai_api_key: str = ""
    anthropic_api_key: str = ""

    # Mode settings
    mode: str = "own"  # own or competitor

    # Audit plan and output
    default_plan: str = ""  # Path to default audit plan (empty = none)
    output_dir: str = ""  # Directory for reports (empty = stdout)

    # Pacing delays (min, max) in seconds
    pacing_delays: dict = field(default_factory=lambda: {
        "off": (0, 0),
        "low": (0.5, 1.5),
        "medium": (1.0, 3.0),
        "high": (2.0, 5.0),
    })


def _safe_load_dotenv(path: Path, **kwargs) -> bool:
    """Load dotenv file, gracefully handling permission errors."""
    if not path.exists():
        return False
    try:
        load_dotenv(path, **kwargs)
        return True
    except PermissionError:
        # File exists but not readable (e.g., /etc/saa/.keys with wrong perms)
        # Skip silently - user keys in ~/.saa/.keys will override anyway
        return False


def load_config() -> Config:
    """Load configuration from .env files with hierarchical precedence.

    Load order (later overrides earlier):
    1. Built-in defaults
    2. /etc/saa/.env (system-wide settings, admin-managed)
    3. ~/.saa/.env and ~/.saa/.keys (user config and keys)
    4. ./.env and ./.keys (project override)
    5. Environment variables (highest priority)

    Note: API keys should be in ~/.saa/.keys (user-private) or env vars,
    not in system-wide /etc/saa/ which would expose keys to all users.
    """
    config = Config()

    # System-wide config (shared settings only, not keys)
    system_dir = Path("/etc/saa")
    _safe_load_dotenv(system_dir / ".env")

    # User config (personal settings and keys)
    user_dir = Path.home() / ".saa"
    _safe_load_dotenv(user_dir / ".env", override=True)
    _safe_load_dotenv(user_dir / ".keys", override=True)

    # Project config (override user)
    _safe_load_dotenv(Path(".env"), override=True)
    _safe_load_dotenv(Path(".keys"), override=True)

    # Override from environment (highest priority)
    config.chromium_path = os.getenv("SAA_CHROMIUM_PATH", config.chromium_path)
    config.default_llm = os.getenv("SAA_DEFAULT_LLM", config.default_llm)
    config.xai_api_key = os.getenv("XAI_API_KEY", "")
    config.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
    config.max_pages = int(os.getenv("SAA_MAX_PAGES", config.max_pages))
    config.default_depth = int(os.getenv("SAA_DEFAULT_DEPTH", config.default_depth))
    config.default_plan = os.getenv("SAA_DEFAULT_PLAN", config.default_plan)
    config.output_dir = os.getenv("SAA_OUTPUT_DIR", config.output_dir)

    return config
