"""Command-line interface for Graphic Agent."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from graphic_agent.config import load_scenario, load_task
from graphic_agent.pipeline import GraphicAgentPipeline

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


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
) -> None:
    """Run a configured visual generation scenario."""

    scenario_config = load_scenario(scenario)
    task = load_task(input_path)
    pipeline = GraphicAgentPipeline(scenario_config, output)
    result = pipeline.run(task)

    table = Table(title="Graphic Agent Run")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Scenario", result.scenario)
    table.add_row("Task", result.task.title)
    table.add_row("Assets", str(len(result.generated_assets)))
    table.add_row("Score", str(result.critique.score))
    table.add_row("Decision", result.revision.action)
    table.add_row("Final Image", result.final_image)
    console.print(table)


if __name__ == "__main__":
    app()
