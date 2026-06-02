"""Shared configuration helpers for the Persuasion Index repo.

The project intentionally keeps secrets out of version control. Copy
`.env.example` to `.env`, edit the values, and these helpers will load them
for command-line scripts such as the LLM lexicon expansion runner.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_ENV_PATH = REPO_ROOT / ".env"
DEFAULT_OPENAI_MODEL = "gpt-5.4-mini"


def _resolve_config_path(path: str | os.PathLike[str] | None = None) -> Path:
    raw_path = path or os.environ.get("PI_CONFIG_FILE") or DEFAULT_ENV_PATH
    config_path = Path(raw_path).expanduser()
    if not config_path.is_absolute():
        config_path = REPO_ROOT / config_path
    return config_path


def _strip_optional_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def load_env_file(
    path: str | os.PathLike[str] | None = None,
    *,
    override: bool = False,
) -> Path:
    """Load KEY=value pairs from a local .env file into os.environ.

    This small parser handles the simple config format used by `.env.example`
    and avoids adding a runtime dependency just for configuration loading.
    Existing environment variables win unless `override=True`.
    """
    config_path = _resolve_config_path(path)
    if not config_path.exists():
        return config_path

    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue

        if override or key not in os.environ:
            os.environ[key] = _strip_optional_quotes(value)

    return config_path


def _optional_env(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str | None
    base_url: str | None
    model: str
    organization: str | None
    project: str | None


def get_openai_config() -> OpenAIConfig:
    """Return OpenAI settings after environment loading has occurred."""
    return OpenAIConfig(
        api_key=_optional_env("OPENAI_API_KEY"),
        base_url=_optional_env("OPENAI_BASE_URL"),
        model=os.environ.get("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip() or DEFAULT_OPENAI_MODEL,
        organization=_optional_env("OPENAI_ORGANIZATION"),
        project=_optional_env("OPENAI_PROJECT"),
    )
