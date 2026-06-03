"""Runtime helpers for provider credentials and failures."""

import os
from collections.abc import Mapping

from graphic_agent.schemas import (
    ModelSpec,
    ProviderEnvironmentStatus,
    ProviderFailure,
    ProviderProfile,
)


def resolve_model_role(provider_profile: ProviderProfile, role: str) -> ModelSpec:
    """Return the model spec assigned to one provider profile role."""

    try:
        return provider_profile.models[role]
    except KeyError as exc:
        available = ", ".join(sorted(provider_profile.models))
        raise ValueError(
            f"Provider profile '{provider_profile.name}' has no model role '{role}'. "
            f"Available roles: {available}"
        ) from exc


def validate_provider_environment(
    provider_profile: ProviderProfile,
    environ: Mapping[str, str] | None = None,
) -> ProviderEnvironmentStatus:
    """Check required provider environment variables without exposing values."""

    if provider_profile.name == "mock":
        return ProviderEnvironmentStatus(
            provider_profile=provider_profile.name,
            ready=True,
        )

    source = os.environ if environ is None else environ
    required_env = [value for value in provider_profile.env.values() if value]
    missing_env = [name for name in required_env if not source.get(name)]

    return ProviderEnvironmentStatus(
        provider_profile=provider_profile.name,
        ready=not missing_env,
        required_env=required_env,
        missing_env=missing_env,
    )


def capture_provider_failure(
    provider_profile: ProviderProfile,
    role: str,
    error: Exception,
    *,
    retryable: bool = False,
) -> ProviderFailure:
    """Convert a provider exception into a structured, secret-safe failure."""

    model_spec = provider_profile.models.get(role)
    provider = model_spec.provider if model_spec else provider_profile.name
    model = model_spec.model if model_spec else "unknown"
    return ProviderFailure(
        provider_profile=provider_profile.name,
        role=role,
        provider=provider,
        model=model,
        reason=str(error),
        retryable=retryable,
    )
