from pathlib import Path

from graphic_agent.config import load_provider_profile
from graphic_agent.costing import record_provider_failure
from graphic_agent.provider_runtime import (
    capture_provider_failure,
    resolve_model_role,
    validate_provider_environment,
)
from graphic_agent.schemas import CostSummary

ROOT = Path(__file__).resolve().parents[1]


def test_missing_real_provider_api_key_is_reported_without_secret_values() -> None:
    profile = load_provider_profile(ROOT / "configs/providers/openai_compatible.yaml")

    status = validate_provider_environment(profile, environ={})

    assert not status.ready
    assert status.required_env == ["OPENAI_API_KEY", "OPENAI_BASE_URL"]
    assert status.missing_env == ["OPENAI_API_KEY", "OPENAI_BASE_URL"]
    assert "sk-" not in status.model_dump_json()


def test_ready_provider_environment_does_not_echo_secret_values() -> None:
    profile = load_provider_profile(ROOT / "configs/providers/openai_compatible.yaml")

    status = validate_provider_environment(
        profile,
        environ={
            "OPENAI_API_KEY": "sk-test-secret",
            "OPENAI_BASE_URL": "https://example.test/v1",
        },
    )

    assert status.ready
    assert status.missing_env == []
    assert "sk-test-secret" not in status.model_dump_json()
    assert "https://example.test/v1" not in status.model_dump_json()


def test_mock_provider_environment_is_ready_without_keys() -> None:
    profile = load_provider_profile(ROOT / "configs/providers/mock.yaml")

    status = validate_provider_environment(profile, environ={})

    assert status.ready
    assert status.required_env == []
    assert status.missing_env == []


def test_provider_failure_is_structured_and_recorded_without_secrets() -> None:
    profile = load_provider_profile(ROOT / "configs/providers/openai_compatible.yaml")
    summary = CostSummary()

    failure = capture_provider_failure(
        profile,
        role="critic",
        error=RuntimeError("quota exceeded for request"),
    )
    record_provider_failure(summary, failure)

    assert failure.provider_profile == "openai_compatible"
    assert failure.role == "critic"
    assert failure.provider == "openai_compatible"
    assert failure.model == "gpt-5.4"
    assert failure.reason == "quota exceeded for request"
    assert summary.provider_failures == [failure]
    assert "sk-" not in summary.model_dump_json()


def test_resolve_openai_compatible_model_roles() -> None:
    profile = load_provider_profile(ROOT / "configs/providers/openai_compatible.yaml")

    planner = resolve_model_role(profile, "planner")
    critic = resolve_model_role(profile, "critic")
    image = resolve_model_role(profile, "image")

    assert planner.model == "gpt-5.4-mini"
    assert critic.model == "gpt-5.4"
    assert image.model == "gpt-image-2"
