"""Command-line interface for Graphic Agent."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from graphic_agent.agents.planner import Planner
from graphic_agent.agents.style_director import StyleDirector
from graphic_agent.config import load_demo_suite, load_provider_profile, load_scenario, load_task
from graphic_agent.costing import combine_suite_estimates, estimate_run_budget
from graphic_agent.pipeline import GraphicAgentPipeline
from graphic_agent.provider_runtime import validate_provider_environment

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


def _default_provider_profile_path(scenario_path: Path) -> Path:
    return scenario_path.resolve().parents[1] / "providers" / "mock.yaml"


@app.callback()
def main() -> None:
    """Graphic Agent command group."""


@app.command()
def run(
    scenario: Annotated[
        Path,
        typer.Option(
            "--scenario",
            "-s",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Path to a scenario YAML file.",
        ),
    ],
    input_path: Annotated[
        Path,
        typer.Option(
            "--input",
            "-i",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Path to a task input YAML file.",
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=False,
            help="Output directory for generated artifacts.",
        ),
    ],
    provider_profile: Annotated[
        Path | None,
        typer.Option(
            "--provider-profile",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Optional provider profile YAML. Defaults to mock when omitted.",
        ),
    ] = None,
) -> None:
    """Run a configured visual generation scenario."""

    scenario_config = load_scenario(scenario)
    profile_config = load_provider_profile(provider_profile) if provider_profile else None
    task = load_task(input_path)
    pipeline = GraphicAgentPipeline(scenario_config, output, provider_profile=profile_config)
    result = pipeline.run(task)

    table = Table(title="Graphic Agent Run")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Scenario", result.scenario)
    table.add_row("Task", result.task.title)
    table.add_row("Assets", str(len(result.generated_assets)))
    table.add_row("Score", str(result.critique.score))
    table.add_row("Decision", result.revision.action)
    table.add_row("Provider Profile", profile_config.name if profile_config else "mock")
    table.add_row("Final Image", result.final_image)
    console.print(table)


@app.command()
def estimate(
    scenario: Annotated[
        Path,
        typer.Option(
            "--scenario",
            "-s",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Path to a scenario YAML file.",
        ),
    ],
    input_path: Annotated[
        Path,
        typer.Option(
            "--input",
            "-i",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Path to a task input YAML file.",
        ),
    ],
    provider_profile: Annotated[
        Path | None,
        typer.Option(
            "--provider-profile",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Optional provider profile YAML. Defaults to configs/providers/mock.yaml.",
        ),
    ] = None,
) -> None:
    """Estimate API budget without generating images or calling providers."""

    scenario_config = load_scenario(scenario)
    profile_path = provider_profile or _default_provider_profile_path(scenario)
    profile_config = load_provider_profile(profile_path)
    task = load_task(input_path)
    style_guide = StyleDirector().create_style_guide(task, scenario_config)
    planned_assets = Planner().plan(task, scenario_config, style_guide)
    estimate_result = estimate_run_budget(
        scenario_config,
        profile_config,
        planned_asset_count=len(planned_assets),
    )

    table = Table(title="Graphic Agent Budget Estimate")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Scenario", scenario_config.name)
    table.add_row("Provider Profile", estimate_result.provider_profile)
    table.add_row("Planned Assets", str(estimate_result.planned_asset_count))
    table.add_row("Retry Buffer Assets", str(estimate_result.retry_buffer_asset_count))
    table.add_row("Baseline Total", str(estimate_result.baseline_total_usd))
    table.add_row("With Retry Buffer", str(estimate_result.with_retry_buffer_usd))
    for name, value in estimate_result.components.items():
        table.add_row(name, str(value))
    console.print(table)


@app.command("estimate-suite")
def estimate_suite(
    suite: Annotated[
        Path,
        typer.Option(
            "--suite",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Path to a demo suite YAML file.",
        ),
    ],
    provider_profile: Annotated[
        Path,
        typer.Option(
            "--provider-profile",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Provider profile YAML used for suite budget estimates.",
        ),
    ],
) -> None:
    """Estimate total API budget for a demo suite without provider calls."""

    suite_config = load_demo_suite(suite)
    suite_root = suite.resolve().parent.parent
    profile_config = load_provider_profile(provider_profile)
    planner = Planner()
    style_director = StyleDirector()
    task_estimates = []

    for suite_task in suite_config.tasks:
        scenario_config = load_scenario(suite_root / suite_task.scenario)
        task = load_task(suite_root / suite_task.input)
        style_guide = style_director.create_style_guide(task, scenario_config)
        planned_assets = planner.plan(task, scenario_config, style_guide)
        task_estimates.append(
            (
                suite_task.name,
                estimate_run_budget(
                    scenario_config,
                    profile_config,
                    planned_asset_count=len(planned_assets),
                ),
            )
        )

    suite_estimate = combine_suite_estimates(
        suite_config.name,
        profile_config,
        task_estimates,
    )

    table = Table(title="Graphic Agent Suite Budget Estimate")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Suite", suite_estimate.suite_name)
    table.add_row("Provider Profile", suite_estimate.provider_profile)
    table.add_row("Total Assets", str(suite_estimate.total_planned_assets))
    table.add_row("Retry Buffer Assets", str(suite_estimate.total_retry_buffer_assets))
    table.add_row("Baseline Total", str(suite_estimate.baseline_total_usd))
    table.add_row("With Retry Buffer", str(suite_estimate.with_retry_buffer_usd))
    for row in suite_estimate.task_estimates:
        table.add_row(
            str(row["name"]),
            (
                f"{row['planned_assets']} assets, "
                f"${row['baseline_total_usd']} baseline, "
                f"${row['with_retry_buffer_usd']} with retry"
            ),
        )
    console.print(table)


@app.command("provider-check")
def provider_check(
    provider_profile: Annotated[
        Path,
        typer.Option(
            "--provider-profile",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Provider profile YAML to validate against environment variables.",
        ),
    ],
) -> None:
    """Check whether a provider profile has its required environment variables."""

    profile_config = load_provider_profile(provider_profile)
    status = validate_provider_environment(profile_config)

    table = Table(title="Graphic Agent Provider Check")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Provider Profile", status.provider_profile)
    table.add_row("Status", "ready" if status.ready else "missing environment")
    table.add_row("Required Env", ", ".join(status.required_env) or "(none)")
    table.add_row("Missing Env", ", ".join(status.missing_env) or "(none)")
    console.print(table)

    if not status.ready:
        raise typer.Exit(code=1)


@app.command("demo-readiness")
def demo_readiness(
    scenario: Annotated[
        Path,
        typer.Option(
            "--scenario",
            "-s",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Path to a scenario YAML file.",
        ),
    ],
    input_path: Annotated[
        Path,
        typer.Option(
            "--input",
            "-i",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Path to a task input YAML file.",
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=False,
            help="Output directory for mock readiness artifacts.",
        ),
    ],
    provider_profile: Annotated[
        Path | None,
        typer.Option(
            "--provider-profile",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Optional provider profile YAML. Real profiles are checked, not run.",
        ),
    ] = None,
) -> None:
    """Check demo readiness without accidentally spending real API budget."""

    scenario_config = load_scenario(scenario)
    profile_path = provider_profile or _default_provider_profile_path(scenario)
    profile_config = load_provider_profile(profile_path)
    task = load_task(input_path)
    style_guide = StyleDirector().create_style_guide(task, scenario_config)
    planned_assets = Planner().plan(task, scenario_config, style_guide)
    estimate_result = estimate_run_budget(
        scenario_config,
        profile_config,
        planned_asset_count=len(planned_assets),
    )
    environment_status = validate_provider_environment(profile_config)

    mock_result_ready = False
    if profile_config.name == "mock":
        mock_result = GraphicAgentPipeline(scenario_config, output).run(task)
        mock_result_ready = mock_result.revision.action in {"accept", "stop"}

    table = Table(title="Graphic Agent Demo Readiness")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")
    table.add_row("Provider Profile", profile_config.name)
    environment_label = "ready" if environment_status.ready else "missing environment"
    table.add_row("Provider Environment", environment_label)
    table.add_row("Missing Env", ", ".join(environment_status.missing_env) or "(none)")
    table.add_row("Budget Estimate", str(estimate_result.with_retry_buffer_usd))
    table.add_row("Mock Pipeline", "ready" if mock_result_ready else "not run")
    table.add_row("Overall", "ready" if environment_status.ready else "blocked")
    console.print(table)

    if not environment_status.ready:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
