import base64
import io
from pathlib import Path

from PIL import Image

from graphic_agent.config import load_provider_profile
from graphic_agent.schemas import AssetSpec, StyleGuide
from graphic_agent.tools.openai_compatible import (
    OpenAICompatibleImageGenerator,
    build_openai_compatible_image_generator,
)

ROOT = Path(__file__).resolve().parents[1]


class FakeImageTransport:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    def generate_image(self, base_url: str, api_key: str, payload: dict) -> dict:
        self.payloads.append(
            {
                "base_url": base_url,
                "api_key": api_key,
                "payload": payload,
            }
        )
        image = Image.new("RGB", (32, 32), (120, 80, 160))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return {"data": [{"b64_json": encoded}]}


def test_openai_compatible_image_generator_returns_structured_asset(tmp_path: Path) -> None:
    profile = load_provider_profile(ROOT / "configs/providers/openai_compatible.yaml")
    transport = FakeImageTransport()
    generator = OpenAICompatibleImageGenerator(
        profile,
        api_key="sk-test-secret",
        base_url="https://example.test/v1",
        transport=transport,
    )
    spec = AssetSpec(
        id="panel_1",
        type="panel",
        category="comic_panel",
        title="Panel 1",
        description="A test panel.",
        purpose="Exercise the real-provider tracer.",
        prompt="Draw a test panel.",
        size=(32, 32),
    )
    style_guide = StyleGuide(name="Test", visual_style="ink")

    asset = generator.generate(spec, style_guide, tmp_path, round_index=1)

    assert Path(asset.path).exists()
    assert asset.metadata["provider"] == "openai_compatible"
    assert asset.metadata["provider_usage"]["model"] == "gpt-image-2"
    assert asset.metadata["provider_usage"]["image_generations"] == 1
    assert "sk-test-secret" not in asset.model_dump_json()
    assert transport.payloads[0]["payload"]["model"] == "gpt-image-2"


def test_build_openai_compatible_image_generator_from_environment() -> None:
    profile = load_provider_profile(ROOT / "configs/providers/openai_compatible.yaml")
    transport = FakeImageTransport()

    generator = build_openai_compatible_image_generator(
        profile,
        environ={
            "OPENAI_API_KEY": "sk-test-secret",
            "OPENAI_BASE_URL": "https://example.test/v1",
        },
        transport=transport,
    )

    assert isinstance(generator, OpenAICompatibleImageGenerator)
