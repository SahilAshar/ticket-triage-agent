"""Configuration models and loader for the ticket triage agent."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class AgentConfigError(RuntimeError):
    """Raised when the agent configuration file cannot be loaded or validated."""


class LLMSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(..., description="Provider/model identifier used for completions.")
    temperature: float = Field(0.0, ge=0.0, le=1.0, description="Softmax temperature; defaults to 0 for determinism.")
    top_p: float = Field(1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter; 1.0 disables sampling.")
    max_tokens: int = Field(2048, ge=1, description="Maximum completion tokens (reasoning + result).")


class RuntimeLimits(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeout_seconds: float = Field(30.0, gt=0.0, description="Wall-clock timeout applied to each ticket execution.")
    tool_budget: int = Field(2, ge=0, description="Maximum number of tool invocations per ticket.")
    idempotency_prefix: str = Field("ticket_id", min_length=1, description="Prefix combined with ticket+model idempotency keys.")


class ToolSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    target: str = Field(
        ...,
        description="Import path or identifier for the tool implementation (e.g., 'tools.retriever:LocalRetriever').",
    )
    params: dict[str, Any] = Field(default_factory=dict, description="Keyword arguments for tool setup.")


class ToolingSettings(BaseModel):
    model_config = ConfigDict(extra="allow")

    retriever: ToolSpec | None = Field(default=None, description="Retriever tool configuration.")
    classifier: ToolSpec | None = Field(default=None, description="Classifier tool configuration.")
    generator: ToolSpec | None = Field(default=None, description="Generator tool configuration.")


class AgentSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    llm: LLMSettings
    runtime: RuntimeLimits = Field(default_factory=RuntimeLimits)
    tooling: ToolingSettings = Field(default_factory=ToolingSettings)


DEFAULT_CONFIG_PATH = Path("config/agent.yaml")


def _read_yaml(path: Path) -> Mapping[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - dependency installation issue surfaced to caller
        raise AgentConfigError(
            "PyYAML is required to load agent configuration. Install project dependencies."
        ) from exc

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except FileNotFoundError as exc:
        raise AgentConfigError(f"Configuration file not found: {path}") from exc
    except OSError as exc:  # pragma: no cover - surfaced directly to caller
        raise AgentConfigError(f"Unable to read configuration file {path}: {exc}") from exc

    if not isinstance(data, Mapping):
        raise AgentConfigError(f"Configuration root must be a mapping, got {type(data)!r}")

    return data


def _validate_settings(payload: Mapping[str, Any]) -> AgentSettings:
    try:
        return AgentSettings.model_validate(payload)
    except ValidationError as exc:  # noqa: E722 - re-raise with context
        raise AgentConfigError("Configuration failed validation") from exc


@lru_cache(maxsize=4)
def load_settings(config_path: str | Path | None = None) -> AgentSettings:
    """Load and cache agent settings from the given YAML file."""

    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    payload = _read_yaml(path)
    return _validate_settings(payload)


def load_settings_from_dict(payload: Mapping[str, Any]) -> AgentSettings:
    """Validate settings from an in-memory dictionary (useful for tests)."""

    return _validate_settings(payload)


def clear_settings_cache() -> None:
    """Reset the cached `load_settings` result (mainly for tests)."""

    load_settings.cache_clear()


__all__ = (
    "AgentConfigError",
    "AgentSettings",
    "LLMSettings",
    "RuntimeLimits",
    "ToolSpec",
    "ToolingSettings",
    "DEFAULT_CONFIG_PATH",
    "load_settings",
    "load_settings_from_dict",
    "clear_settings_cache",
)
