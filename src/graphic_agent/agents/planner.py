"""Deterministic planning agent for the MVP.

The planner intentionally produces structured `AssetSpec` objects instead of
free-form text. Future LLM planners should preserve this contract.
"""

from graphic_agent.schemas import AssetSpec, ScenarioConfig, StyleGuide, VisualTask


class Planner:
    """Plan visual assets from a task and scenario configuration."""

    def plan(
        self,
        task: VisualTask,
        scenario: ScenarioConfig,
        style_guide: StyleGuide,
    ) -> list[AssetSpec]:
        if scenario.name == "story_comic":
            return self._plan_story_comic(task, scenario, style_guide)
        if scenario.name == "game_assets":
            return self._plan_game_assets(task, scenario, style_guide)
        return self._plan_generic_visual_composition(task, scenario, style_guide)

    def _plan_story_comic(
        self,
        task: VisualTask,
        scenario: ScenarioConfig,
        style_guide: StyleGuide,
    ) -> list[AssetSpec]:
        min_panels, max_panels = scenario.assets.get("panel_count_range", [4, 8])
        default_panel_count = scenario.assets.get("default_panel_count", 4)
        requested = int(task.constraints.get("panel_count", default_panel_count))
        panel_count = min(max(requested, int(min_panels)), int(max_panels))
        prompt_base = self._style_prompt(task, style_guide)

        assets: list[AssetSpec] = [
            AssetSpec(
                id="character_reference_robot",
                type="character_reference",
                category="character",
                title="Main Character Reference",
                description="A consistent reference sheet for the protagonist and companion.",
                purpose="Maintain cross-panel character consistency.",
                prompt=(
                    f"{prompt_base}. Character reference sheet for the main character in: "
                    f"{task.prompt}"
                ),
                order=0,
                size=(768, 768),
            )
        ]

        beats = [
            (
                "Opening",
                "Establish the setting, weather, and protagonist goal.",
                "Where did the kitten go?",
            ),
            ("Clue", "Show the protagonist discovering a clue or obstacle.", "A tiny pawprint!"),
            (
                "Tension",
                "Increase emotional stakes with a larger dramatic composition.",
                "Hold on, I am coming.",
            ),
            ("Resolution", "Resolve the search with a warm emotional payoff.", "Found you."),
            ("Aftermath", "Show a quiet beat that reinforces the theme.", "Let us go home."),
            ("Callback", "End with a visual callback or gentle joke.", "Mission complete."),
            (
                "Wide Moment",
                "Use a wider scene to show world detail and mood.",
                "The city feels kinder now.",
            ),
            ("Final Button", "Close with a memorable final image.", "Tomorrow, another delivery."),
        ]
        for index in range(panel_count):
            title, beat, dialogue = beats[index]
            assets.append(
                AssetSpec(
                    id=f"panel_{index + 1}",
                    type="panel",
                    category="comic_panel",
                    title=f"Panel {index + 1}: {title}",
                    description=beat,
                    purpose="Tell one beat of the comic narrative.",
                    prompt=(
                        f"{prompt_base}. Comic panel {index + 1}/{panel_count}. "
                        f"Story: {task.prompt}. Beat: {beat}. Keep character designs consistent."
                    ),
                    order=index + 1,
                    size=(900, 700),
                    metadata={"dialogue": dialogue},
                )
            )
        return assets

    def _plan_game_assets(
        self,
        task: VisualTask,
        scenario: ScenarioConfig,
        style_guide: StyleGuide,
    ) -> list[AssetSpec]:
        categories = [str(value) for value in scenario.assets.get("categories", ["props"])]
        per_category = int(scenario.assets.get("assets_per_category", 2))
        prompt_base = self._style_prompt(task, style_guide)
        assets: list[AssetSpec] = []
        order = 0
        for category in categories:
            for index in range(per_category):
                order += 1
                title = f"{category.replace('_', ' ').title()} {index + 1}"
                assets.append(
                    AssetSpec(
                        id=f"{category}_{index + 1}",
                        type="game_asset",
                        category=category,
                        title=title,
                        description=(
                            f"A production-ready 2D {category} asset for the requested game world."
                        ),
                        purpose="Populate a coherent prototype asset pack.",
                        prompt=(
                            f"{prompt_base}. Isolated 2D game asset. Category: {category}. "
                            f"Design document: {task.prompt}. "
                            "Transparent-background friendly composition."
                        ),
                        order=order,
                        size=(768, 768),
                    )
                )
        return assets

    def _plan_generic_visual_composition(
        self,
        task: VisualTask,
        scenario: ScenarioConfig,
        style_guide: StyleGuide,
    ) -> list[AssetSpec]:
        asset_types = scenario.assets.get("types", ["visual_asset"])
        prompt_base = self._style_prompt(task, style_guide)
        return [
            AssetSpec(
                id=f"asset_{index + 1}",
                type=str(asset_type),
                category="generic",
                title=f"{asset_type} {index + 1}",
                description=f"Generic visual asset for {scenario.name}.",
                purpose="Support the configured visual composition workflow.",
                prompt=f"{prompt_base}. {task.prompt}. Asset type: {asset_type}.",
                order=index + 1,
            )
            for index, asset_type in enumerate(asset_types)
        ]

    def _style_prompt(self, task: VisualTask, style_guide: StyleGuide) -> str:
        palette = ", ".join(style_guide.palette)
        negative = f" Avoid: {style_guide.negative_prompt}." if style_guide.negative_prompt else ""
        return (
            f"{style_guide.visual_style}; mood: {style_guide.mood}; palette: {palette}. "
            f"Task title: {task.title}.{negative}"
        )
