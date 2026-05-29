"""Style guide generation."""

from graphic_agent.schemas import ScenarioConfig, StyleGuide, VisualTask


class StyleDirector:
    """Create a reusable visual style memory from task and scenario inputs."""

    def create_style_guide(self, task: VisualTask, scenario: ScenarioConfig) -> StyleGuide:
        style = task.style
        visual_style = str(style.get("visual_style") or "clean digital illustration")
        palette = [str(value) for value in style.get("palette", [])]
        if not palette:
            palette = ["balanced neutrals", "clear accent color", "soft background tone"]
        mood = str(style.get("mood") or "coherent and readable")
        typography = str(style.get("typography") or "legible post-processed labels")
        negative_prompt = str(task.constraints.get("avoid") or "")
        notes = [
            f"Scenario: {scenario.name}",
            "Keep style consistent across all generated assets.",
            "Prefer clear silhouettes and readable compositions.",
        ]
        return StyleGuide(
            name=f"{task.title} Style Guide",
            visual_style=visual_style,
            palette=palette,
            mood=mood,
            typography=typography,
            negative_prompt=negative_prompt,
            notes=notes,
        )
