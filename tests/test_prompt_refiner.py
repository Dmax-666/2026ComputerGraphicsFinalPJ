import json
from pathlib import Path

from graphic_agent.agents.prompt_refiner import LLMPromptRefiner
from graphic_agent.config import load_provider_profile, load_scenario, load_task
from graphic_agent.schemas import AssetSpec, ProviderUsage, StyleGuide
from graphic_agent.tools.openai_compatible import (
    OpenAICompatibleTextGenerator,
    build_openai_compatible_text_generator,
)

ROOT = Path(__file__).resolve().parents[1]


class FakeTextTransport:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    def complete_chat(self, base_url: str, api_key: str, payload: dict) -> dict:
        self.payloads.append(
            {
                "base_url": base_url,
                "api_key": api_key,
                "payload": payload,
            }
        )
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "assets": [
                                    {
                                        "id": "panel_1",
                                        "prompt": "Refined cinematic robot cat panel prompt.",
                                    }
                                ]
                            }
                        )
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }


class FakeTextGenerator:
    def complete(self, system_prompt: str, user_prompt: str) -> tuple[str, ProviderUsage]:
        return (
            json.dumps(
                {
                    "assets": [
                        {
                            "id": "panel_1",
                            "prompt": "Refined cinematic robot cat panel prompt.",
                        }
                    ]
                }
            ),
            ProviderUsage(
                role="planner",
                provider_profile="openai_compatible",
                provider="openai_compatible",
                model="gpt-5.4-mini",
                prompt_tokens=10,
                completion_tokens=5,
                estimated_cost_usd=0.002,
            ),
        )


def test_openai_compatible_text_generator_returns_content_and_usage() -> None:
    profile = load_provider_profile(ROOT / "configs/providers/openai_compatible.yaml")
    transport = FakeTextTransport()
    generator = OpenAICompatibleTextGenerator(
        profile,
        "planner",
        api_key="sk-test-secret",
        base_url="https://text.example.test/v1",
        transport=transport,
    )

    content, usage = generator.complete("system", "user")

    assert "panel_1" in content
    assert usage.role == "planner"
    assert usage.model == "gpt-5.4-mini"
    assert usage.prompt_tokens == 10
    assert usage.completion_tokens == 5
    assert "sk-test-secret" not in usage.model_dump_json()
    assert transport.payloads[0]["payload"]["model"] == "gpt-5.4-mini"


def test_build_text_generator_uses_text_environment_variables() -> None:
    profile = load_provider_profile(ROOT / "configs/providers/openai_compatible.yaml")
    transport = FakeTextTransport()

    generator = build_openai_compatible_text_generator(
        profile,
        "planner",
        environ={
            "OPENAI_TEXT_API_KEY": "sk-test-secret",
            "OPENAI_TEXT_BASE_URL": "https://text.example.test/v1",
        },
        transport=transport,
    )

    assert isinstance(generator, OpenAICompatibleTextGenerator)


def test_llm_prompt_refiner_updates_matching_asset_prompts() -> None:
    scenario = load_scenario(ROOT / "configs/scenarios/story_comic.yaml")
    task = load_task(ROOT / "examples/story_comic_robot_cat.yaml")
    style_guide = StyleGuide(name="Test", visual_style="comic")
    spec = AssetSpec(
        id="panel_1",
        type="panel",
        category="comic_panel",
        title="Panel 1",
        description="A panel.",
        purpose="Tell the story.",
        prompt="Original prompt.",
    )
    refiner = LLMPromptRefiner(FakeTextGenerator())

    refined, report, usage = refiner.refine(
        task=task,
        scenario=scenario,
        style_guide=style_guide,
        specs=[spec],
    )

    assert refined[0].prompt == "Refined cinematic robot cat panel prompt."
    assert refined[0].metadata["original_prompt"] == "Original prompt."
    assert report["enabled"] is True
    assert report["assets"][0]["status"] == "refined"
    assert usage[0].role == "planner"
