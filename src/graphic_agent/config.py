"""Configuration loading helpers."""

from pathlib import Path
from typing import Any

from graphic_agent.schemas import ProviderProfile, ScenarioConfig, VisualTask


def _load_yaml_library():
    try:
        import yaml  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        message = (
            "PyYAML is required to load .yaml files. Install dependencies with "
            '`python -m pip install -e ".[dev]"`.'
        )
        raise RuntimeError(message) from exc
    return yaml


def load_yaml(path: Path | str) -> dict[str, Any]:
    """Load a YAML document as a dictionary."""

    yaml = _load_yaml_library()
    resolved = Path(path)
    with resolved.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML file must contain a mapping at the top level: {resolved}")
    return data


def load_scenario(path: Path | str) -> ScenarioConfig:
    """Load and validate a scenario config."""

    return ScenarioConfig(**load_yaml(path))


def load_provider_profile(path: Path | str) -> ProviderProfile:
    """Load and validate a provider profile config."""

    return ProviderProfile(**load_yaml(path))


def resolve_provider_profile(name: str, providers_dir: Path | str) -> ProviderProfile:
    """Load a provider profile by name from a provider profiles directory."""

    return load_provider_profile(Path(providers_dir) / f"{name}.yaml")


def load_task(path: Path | str) -> VisualTask:
    """Load and validate a user task input file."""

    return VisualTask.from_payload(load_yaml(path))
