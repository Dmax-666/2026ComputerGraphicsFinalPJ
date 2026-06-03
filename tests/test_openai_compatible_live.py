"""Opt-in live smoke test for the OpenAI-compatible image provider.

This file is intentionally skipped by default. It should only run when a
teammate explicitly opts in on a funded API account.
"""

import os
from pathlib import Path

import pytest

from graphic_agent.config import load_provider_profile
from graphic_agent.schemas import AssetSpec, StyleGuide
from graphic_agent.tools.openai_compatible import build_openai_compatible_image_generator

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ENV = ["GRAPHIC_AGENT_RUN_REAL_API", "OPENAI_API_KEY", "OPENAI_BASE_URL"]

pytestmark = pytest.mark.skipif(
    not (
        os.environ.get("GRAPHIC_AGENT_RUN_REAL_API") == "1"
        and all(os.environ.get(name) for name in REQUIRED_ENV[1:])
    ),
    reason=(
        "Live OpenAI-compatible smoke test skipped. Set GRAPHIC_AGENT_RUN_REAL_API=1 "
        "plus OPENAI_API_KEY and OPENAI_BASE_URL to run it."
    ),
)


def test_openai_compatible_live_image_generation(tmp_path: Path) -> None:
    profile = load_provider_profile(ROOT / "configs/providers/openai_compatible.yaml")
    generator = build_openai_compatible_image_generator(profile)
    spec = AssetSpec(
        id="live_smoke_panel",
        type="panel",
        category="smoke_test",
        title="Live Smoke Panel",
        description="A tiny visual smoke test for the OpenAI-compatible provider.",
        purpose="Verify that the provider can return a structured GeneratedAsset.",
        prompt="A simple clean digital illustration of a blue square on white background.",
        size=(1024, 1024),
    )
    style_guide = StyleGuide(name="Live Smoke", visual_style="minimal clean vector style")

    asset = generator.generate(spec, style_guide, tmp_path, round_index=1)

    assert Path(asset.path).exists()
    assert asset.metadata["provider"] == "openai_compatible"
    assert asset.metadata["provider_usage"]["image_generations"] == 1
    assert asset.metadata["provider_usage"]["estimated_cost_usd"] > 0
