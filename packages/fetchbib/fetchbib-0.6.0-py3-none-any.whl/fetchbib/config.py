"""User configuration for fetchbib.

Reads and writes a JSON config file at ~/.config/fetchbib/config.json.
"""

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "fetchbib"
CONFIG_FILE = CONFIG_DIR / "config.json"

OPENALEX_API_KEY_ENV = "OPENALEX_API_KEY"


def get_openalex_api_key() -> str | None:
    """Return the OpenAlex API key, checking env var first, then config file.

    Returns None if no key is configured.
    """
    env_key = os.environ.get(OPENALEX_API_KEY_ENV)
    if env_key:
        return env_key
    cfg = _read_config()
    return cfg.get("openalex_api_key")


def set_openalex_api_key(key: str) -> None:
    """Persist the OpenAlex API key to the config file."""
    cfg = _read_config()
    cfg["openalex_api_key"] = key
    _write_config(cfg)


def _get_bool(key: str, default: bool = False) -> bool:
    """Return a boolean config value, with a default if not set."""
    return _read_config().get(key, default)


def _set_bool(key: str, value: bool) -> None:
    """Persist a boolean config value."""
    cfg = _read_config()
    cfg[key] = value
    _write_config(cfg)


def get_protect_titles() -> bool:
    """Return True if titles should be double-braced."""
    return _get_bool("protect_titles")


def set_protect_titles(enabled: bool) -> None:
    """Persist the protect_titles setting."""
    _set_bool("protect_titles", enabled)


def get_exclude_issn() -> bool:
    """Return True if ISSN should be excluded from BibTeX entries."""
    return _get_bool("exclude_issn")


def set_exclude_issn(enabled: bool) -> None:
    """Persist the exclude_issn setting."""
    _set_bool("exclude_issn", enabled)


def get_exclude_doi() -> bool:
    """Return True if DOI should be excluded from BibTeX entries."""
    return _get_bool("exclude_doi")


def set_exclude_doi(enabled: bool) -> None:
    """Persist the exclude_doi setting."""
    _set_bool("exclude_doi", enabled)


def _read_config() -> dict:
    """Read the config file, returning an empty dict if it doesn't exist."""
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE) as f:
        return json.load(f)


def _write_config(cfg: dict) -> None:
    """Write the config dict to disk, creating the directory if needed."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
