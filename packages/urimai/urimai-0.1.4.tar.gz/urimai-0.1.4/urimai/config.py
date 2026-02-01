"""Configuration management for urimai."""

import os
import tomllib
from pathlib import Path

import keyring
import tomli_w

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
URIMAI_HOME = Path.home() / ".urimai"
CONFIG_FILE = URIMAI_HOME / "config.toml"
METADATA_DB = URIMAI_HOME / "metadata.db"
CSV_DATABASES_DIR = URIMAI_HOME / "csv_databases"

SERVICE_NAME = "urimai"

# ---------------------------------------------------------------------------
# Default config values (written on first setup)
# ---------------------------------------------------------------------------
DEFAULT_CONFIG: dict = {
    "user": {"name": ""},
    "provider": {
        "default": "google",
        "google_model": "gemini-2.5-flash",
        "openai_model": "gpt-4o",
    },
    "settings": {
        "sample_rows": 5,
        "query_timeout": 60,
        "max_retry_attempts": 3,
        "max_plan_revisions": 2,
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ensure_data_dir() -> None:
    """Create ~/.urimai/ and sub-directories if they don't exist."""
    URIMAI_HOME.mkdir(parents=True, exist_ok=True)
    CSV_DATABASES_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load config from ~/.urimai/config.toml, falling back to defaults."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            return tomllib.load(f)
    return DEFAULT_CONFIG.copy()


def save_config(data: dict) -> None:
    """Write config dict to ~/.urimai/config.toml."""
    ensure_data_dir()
    with open(CONFIG_FILE, "wb") as f:
        tomli_w.dump(data, f)


def is_setup_complete() -> bool:
    """Return True if the config file exists."""
    return CONFIG_FILE.exists()


# ---------------------------------------------------------------------------
# Keyring integration
# ---------------------------------------------------------------------------

def store_api_key(provider: str, key: str) -> None:
    """Store an API key in the system keyring."""
    try:
        keyring.set_password(SERVICE_NAME, provider, key)
    except Exception:
        pass  # keyring unavailable (headless, Docker)


def get_api_key(provider: str) -> str:
    """Retrieve API key with fallback chain: env var -> keyring -> empty.

    Env var names checked (in order):
      1. <PROVIDER>_API_KEY  (e.g. GOOGLE_API_KEY, OPENAI_API_KEY)
      2. URIMAI_API_KEY      (generic override)
    """
    # 1. Provider-specific env var
    env_key = os.environ.get(f"{provider.upper()}_API_KEY", "")
    if env_key:
        return env_key

    # 2. Generic env var
    generic = os.environ.get("URIMAI_API_KEY", "")
    if generic:
        return generic

    # 3. System keyring
    try:
        stored = keyring.get_password(SERVICE_NAME, provider)
        if stored:
            return stored
    except Exception:
        pass  # keyring unavailable

    return ""


def _has_env_api_keys() -> bool:
    """Return True if any API key env vars are set (skip setup gate)."""
    return bool(
        os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("URIMAI_API_KEY")
    )


# ---------------------------------------------------------------------------
# Config class (backward-compatible via metaclass)
# ---------------------------------------------------------------------------

class _ConfigMeta(type):
    """Metaclass that resolves Config attributes dynamically from TOML + keyring."""

    def __getattr__(cls, name: str):
        data = load_config()
        mapping = {
            "PROVIDER": lambda: cls._provider_override or data.get("provider", {}).get("default", "google"),
            "GOOGLE_API_KEY": lambda: get_api_key("google"),
            "OPENAI_API_KEY": lambda: get_api_key("openai"),
            "MODEL_NAME": lambda: data.get("provider", {}).get("google_model", "gemini-2.5-flash"),
            "OPENAI_MODEL_NAME": lambda: data.get("provider", {}).get("openai_model", "gpt-4o"),
            "METADATA_DB_PATH": lambda: str(METADATA_DB),
            "DEFAULT_SAMPLE_ROWS": lambda: data.get("settings", {}).get("sample_rows", 5),
            "QUERY_TIMEOUT": lambda: data.get("settings", {}).get("query_timeout", 60),
            "MAX_RETRY_ATTEMPTS": lambda: data.get("settings", {}).get("max_retry_attempts", 3),
            "MAX_PLAN_REVISIONS": lambda: data.get("settings", {}).get("max_plan_revisions", 2),
        }
        if name in mapping:
            return mapping[name]()
        raise AttributeError(f"Config has no attribute '{name}'")


class Config(metaclass=_ConfigMeta):
    """Application configuration backed by ~/.urimai/config.toml + system keyring."""

    _provider_override: str | None = None

    @classmethod
    def validate(cls) -> None:
        """Validate that the active provider has an API key."""
        provider = cls._provider_override or cls.PROVIDER
        if not get_api_key(provider):
            raise RuntimeError(
                f"API key for '{provider}' not found. "
                f"Run 'urim setup' or set {provider.upper()}_API_KEY."
            )

    @classmethod
    def get_metadata_db_path(cls) -> Path:
        """Get the metadata database path."""
        ensure_data_dir()
        return METADATA_DB
