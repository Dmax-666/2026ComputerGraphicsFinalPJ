from pathlib import Path

from typer.testing import CliRunner

from graphic_agent.cli import app

ROOT = Path(__file__).resolve().parents[1]


def test_estimate_command_reports_budget_without_running_pipeline() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "estimate",
            "--scenario",
            str(ROOT / "configs/scenarios/story_comic.yaml"),
            "--input",
            str(ROOT / "examples/story_comic_robot_cat.yaml"),
            "--provider-profile",
            str(ROOT / "configs/providers/openai_compatible.yaml"),
        ],
    )

    assert result.exit_code == 0
    assert "openai_compatible" in result.stdout
    assert "Planned Assets" in result.stdout
    assert "5" in result.stdout
    assert "Baseline Total" in result.stdout
    assert "0.271" in result.stdout
    assert "With Retry Buffer" in result.stdout
    assert "0.801" in result.stdout


def test_estimate_command_defaults_to_mock_profile() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "estimate",
            "--scenario",
            str(ROOT / "configs/scenarios/story_comic.yaml"),
            "--input",
            str(ROOT / "examples/story_comic_robot_cat.yaml"),
        ],
    )

    assert result.exit_code == 0
    assert "mock" in result.stdout
    assert "0.0" in result.stdout


def test_provider_check_reports_missing_env_without_secret_values() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "provider-check",
            "--provider-profile",
            str(ROOT / "configs/providers/openai_compatible.yaml"),
        ],
        env={},
    )

    assert result.exit_code == 1
    assert "openai_compatible" in result.stdout
    assert "Missing Env" in result.stdout
    assert "OPENAI_API_KEY" in result.stdout
    assert "OPENAI_BASE_URL" in result.stdout
    assert "sk-" not in result.stdout


def test_provider_check_passes_for_mock_profile() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "provider-check",
            "--provider-profile",
            str(ROOT / "configs/providers/mock.yaml"),
        ],
        env={},
    )

    assert result.exit_code == 0
    assert "mock" in result.stdout
    assert "ready" in result.stdout.lower()


def test_demo_readiness_runs_mock_pipeline(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "demo-readiness",
            "--scenario",
            str(ROOT / "configs/scenarios/story_comic.yaml"),
            "--input",
            str(ROOT / "examples/story_comic_robot_cat.yaml"),
            "--output",
            str(tmp_path / "ready"),
        ],
    )

    assert result.exit_code == 0
    assert "ready" in result.stdout.lower()
    assert "Budget Estimate" in result.stdout
    assert "Mock Pipeline" in result.stdout
    assert (tmp_path / "ready/reports/result.json").exists()


def test_demo_readiness_does_not_run_real_provider_when_env_missing(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "demo-readiness",
            "--scenario",
            str(ROOT / "configs/scenarios/story_comic.yaml"),
            "--input",
            str(ROOT / "examples/story_comic_robot_cat.yaml"),
            "--output",
            str(tmp_path / "real"),
            "--provider-profile",
            str(ROOT / "configs/providers/openai_compatible.yaml"),
        ],
        env={},
    )

    assert result.exit_code == 1
    assert "missing environment" in result.stdout.lower()
    assert "OPENAI_API_KEY" in result.stdout
    assert not (tmp_path / "real/reports/result.json").exists()
