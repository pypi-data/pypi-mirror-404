from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any

DEFAULT_ENDPOINT = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"


class ConfigError(RuntimeError):
    pass


@dataclass
class Settings:
    endpoint: str | None = None
    api_key: str | None = None
    model: str | None = None
    shell: str | None = None


def config_path() -> Path:
    override = os.getenv("CLANKER_CONFIG")
    if override:
        return Path(override).expanduser()
    base = os.getenv("XDG_CONFIG_HOME")
    if base:
        base_path = Path(base)
    else:
        base_path = Path.home() / ".config"
    return base_path / "clanker" / "config.json"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in config file: {path}") from exc


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        return {}
    return _read_json(path)


def save_config(data: dict[str, Any]) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(tmp_path, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def redact_api_key(value: str | None) -> str | None:
    if not value:
        return value
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def detect_shell() -> str:
    shell_path = os.getenv("SHELL", "")
    shell_name = os.path.basename(shell_path)
    if shell_name:
        return shell_name
    return "fish"


def resolve_settings(config: dict[str, Any], overrides: dict[str, Any] | None = None) -> Settings:
    overrides = overrides or {}

    def pick(key: str, env_var: str) -> str | None:
        if overrides.get(key):
            return overrides[key]
        env_value = os.getenv(env_var)
        if env_value:
            return env_value
        value = config.get(key)
        if isinstance(value, str) and value:
            return value
        return None

    endpoint = pick("endpoint", "CLANKER_ENDPOINT") or DEFAULT_ENDPOINT
    api_key = pick("api_key", "CLANKER_API_KEY")
    model = pick("model", "CLANKER_MODEL")
    shell = pick("shell", "CLANKER_SHELL") or detect_shell()

    return Settings(endpoint=endpoint, api_key=api_key, model=model, shell=shell)


def require_settings(settings: Settings) -> None:
    missing = []
    if not settings.api_key:
        missing.append("api_key")
    if not settings.model:
        missing.append("model")
    if missing:
        raise ConfigError(
            "Missing required settings: "
            + ", ".join(missing)
            + ". Run `clanker config` or set CLANKER_API_KEY/CLANKER_MODEL."
        )
