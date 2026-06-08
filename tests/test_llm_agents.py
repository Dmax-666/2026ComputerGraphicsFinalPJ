import json
from pathlib import Path

from PIL import Image

from graphic_agent.agents.llm_agents import (
    LLMCritic,
    LLMPlanner,
    LLMRevisionController,
    LLMStyleDirector,
)
from graphic_agent.config import load_scenario, load_task
from graphic_agent.schemas import (
    AssetSpec,
    CompositionSpec,
    GeneratedAsset,
    ProviderUsage,
    StyleGuide,
)

ROOT = Path(__file__).resolve().parents[1]


class FakeLLMTextGenerator:
    def __init__(self, payload: dict, role: str = "planner") -> None:
        self.payload = payload
        self.role = role
        self.calls = 0

    def complete(self, system_prompt: str, user_prompt: str) -> tuple[str, ProviderUsage]:
        self.calls += 1
        return self._response()

    def complete_messages(self, messages: list[dict]) -> tuple[str, ProviderUsage]:
        self.calls += 1
        return self._response()

    def _response(self) -> tuple[str, ProviderUsage]:
        return (
            json.dumps(self.payload),
            ProviderUsage(
                role=self.role,
                provider_profile="openai_compatible",
                provider="openai_compatible",
                model="gpt-5.4-mini" if self.role == "planner" else "gpt-5.4",
                prompt_tokens=10,
                completion_tokens=5,
                estimated_cost_usd=0.002,
            ),
        )


def test_llm_style_director_enriches_style_guide() -> None:
    scenario = load_scenario(ROOT / "configs/scenarios/story_comic.yaml")
    task = load_task(ROOT / "examples/story_comic_robot_cat.yaml")
    agent = LLMStyleDirector(
        FakeLLMTextGenerator(
            {
                "name": "LLM Style",
                "visual_style": "rainy cinematic comic with warm robot lighting",
                "palette": ["amber", "cobalt", "rain gray"],
                "mood": "hopeful",
                "typography": "clean comic lettering",
                "negative_prompt": "horror",
                "notes": ["keep robot silhouette consistent"],
            }
        )
    )

    style = agent.create_style_guide(task, scenario)

    assert style.name == "LLM Style"
    assert "robot" in style.visual_style
    assert agent.last_report["status"] == "llm_generated"
    assert agent.last_usage[0].role == "planner"


def test_llm_planner_returns_structured_asset_specs() -> None:
    scenario = load_scenario(ROOT / "configs/scenarios/story_comic.yaml")
    task = load_task(ROOT / "examples/story_comic_robot_cat.yaml")
    style = StyleGuide(name="Style", visual_style="comic")
    agent = LLMPlanner(
        FakeLLMTextGenerator(
            {
                "assets": [
                    {
                        "id": "panel_1",
                        "type": "panel",
                        "category": "comic_panel",
                        "title": "Rainy clue",
                        "description": "Robot finds a pawprint.",
                        "purpose": "Advance the story.",
                        "prompt": "Draw the robot finding a glowing pawprint.",
                        "order": 1,
                        "size": [900, 700],
                        "depends_on": [],
                        "metadata": {"dialogue": "A clue."},
                    }
                ]
            }
        )
    )

    specs = agent.plan(task, scenario, style)

    assert len(specs) == 1
    assert specs[0].id == "panel_1"
    assert specs[0].size == (900, 700)
    assert agent.last_report["status"] == "llm_generated"


def test_llm_critic_adds_visual_review_evaluator(tmp_path: Path) -> None:
    scenario = load_scenario(ROOT / "configs/scenarios/story_comic.yaml")
    image_path = tmp_path / "final.png"
    Image.new("RGB", (900, 700), (20, 40, 80)).save(image_path)
    spec = AssetSpec(
        id="panel_1",
        type="panel",
        category="comic_panel",
        title="Panel 1",
        description="A panel.",
        purpose="Tell story.",
        prompt="Prompt.",
        size=(900, 700),
    )
    asset = GeneratedAsset(spec_id="panel_1", path=str(image_path), prompt="Prompt.", seed=1)
    composition = CompositionSpec(
        type="comic_page",
        page_size=(900, 700),
        output_path=str(image_path),
    )
    agent = LLMCritic(
        FakeLLMTextGenerator(
            {
                "score": 0.92,
                "passed": True,
                "summary": "Story and image are coherent.",
                "issues": [],
            },
            role="critic",
        )
    )

    report = agent.review(scenario, [spec], [asset], composition)

    assert report.passed
    assert "llm_vision_critic" in report.evaluator_names
    assert agent.last_report["status"] == "llm_vision_reviewed"
    assert agent.last_usage[0].role == "critic"


def test_llm_revision_controller_rewrites_failed_asset_prompt() -> None:
    scenario = load_scenario(ROOT / "configs/scenarios/story_comic.yaml")
    spec = AssetSpec(
        id="panel_1",
        type="panel",
        category="comic_panel",
        title="Panel 1",
        description="A panel.",
        purpose="Tell story.",
        prompt="Prompt.",
    )
    agent = LLMRevisionController(
        FakeLLMTextGenerator(
            {
                "action": "retry_assets",
                "rationale": "Panel needs a clearer cat silhouette.",
                "retry_asset_ids": ["panel_1"],
                "prompt_rewrites": {"panel_1": "Draw a clearer cat silhouette in the rain."},
                "reasoning_trace": ["Retry panel_1 for clearer story readability."],
            }
        )
    )
    from graphic_agent.schemas import CritiqueIssue, CritiqueReport

    report = CritiqueReport(
        score=0.5,
        passed=False,
        summary="Issue found.",
        issues=[
            CritiqueIssue(
                asset_id="panel_1",
                severity="medium",
                category="story_readability",
                message="Cat is not visible.",
                recommendation="Make the cat clearer.",
            )
        ],
    )

    decision = agent.decide(report, scenario, 1, [spec])

    assert decision.action == "retry_assets"
    assert decision.prompt_rewrites["panel_1"] == "Draw a clearer cat silhouette in the rain."
    assert agent.last_report["status"] == "llm_decided"


def test_llm_revision_controller_respects_max_round_budget() -> None:
    scenario = load_scenario(ROOT / "configs/scenarios/story_comic.yaml")
    spec = AssetSpec(
        id="panel_1",
        type="panel",
        category="comic_panel",
        title="Panel 1",
        description="A panel.",
        purpose="Tell story.",
        prompt="Prompt.",
    )
    agent = LLMRevisionController(
        FakeLLMTextGenerator(
            {
                "action": "retry_assets",
                "rationale": "Try again.",
                "retry_asset_ids": ["panel_1"],
                "prompt_rewrites": {"panel_1": "Retry prompt."},
                "reasoning_trace": ["Retry requested."],
            }
        )
    )
    from graphic_agent.schemas import CritiqueIssue, CritiqueReport

    report = CritiqueReport(
        score=0.5,
        passed=False,
        summary="Issue found.",
        issues=[
            CritiqueIssue(
                asset_id="panel_1",
                severity="medium",
                category="story_readability",
                message="Cat is not visible.",
                recommendation="Make the cat clearer.",
            )
        ],
    )

    decision = agent.decide(report, scenario, scenario.revision.max_rounds, [spec])

    assert decision.action == "stop"
