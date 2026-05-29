"""Image generation tools.

The MVP ships with a deterministic mock generator so the full framework can be
tested without model credentials. Real providers should implement the same
`generate` method and return `GeneratedAsset` objects.
"""

import hashlib
import random
import re
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from graphic_agent.schemas import AssetSpec, GeneratedAsset, StyleGuide


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower()).strip("-")
    return slug or "asset"


def _color_from_text(value: str) -> tuple[int, int, int]:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    red = 80 + int(digest[0:2], 16) % 120
    green = 80 + int(digest[2:4], 16) % 120
    blue = 80 + int(digest[4:6], 16) % 120
    return red, green, blue


def _wrapped_lines(text: str, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [text]:
        lines.extend(textwrap.wrap(paragraph, width=width) or [""])
    return lines


class MockImageGenerator:
    """Deterministic placeholder image generator."""

    def generate(
        self,
        spec: AssetSpec,
        style_guide: StyleGuide,
        output_dir: Path,
        round_index: int = 1,
    ) -> GeneratedAsset:
        seed = int(hashlib.sha256(f"{spec.id}:{round_index}".encode()).hexdigest()[:8], 16)
        random.seed(seed)
        width, height = spec.size
        background = _color_from_text(spec.prompt + style_guide.visual_style)
        accent = tuple(min(255, channel + 48) for channel in background)
        image = Image.new("RGB", (width, height), background)
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()

        draw.rectangle((16, 16, width - 16, height - 16), outline=(255, 255, 255), width=4)
        draw.rectangle((32, 32, width - 32, 120), fill=accent)
        draw.text((48, 48), spec.title[:80], fill=(20, 20, 20), font=font)

        text = (
            f"{spec.type} / {spec.category}\n{spec.description}\nStyle: {style_guide.visual_style}"
        )
        y = 150
        for line in _wrapped_lines(text, max(24, width // 12))[:16]:
            draw.text((48, y), line, fill=(255, 255, 255), font=font)
            y += 22

        if spec.metadata.get("dialogue"):
            bubble_height = min(120, max(72, height // 5))
            bubble = (40, height - bubble_height - 40, width - 40, height - 40)
            draw.rounded_rectangle(
                bubble,
                radius=24,
                fill=(255, 255, 255),
                outline=(20, 20, 20),
                width=3,
            )
            dialogue = str(spec.metadata["dialogue"])
            y = bubble[1] + 18
            for line in _wrapped_lines(dialogue, max(20, width // 14))[:4]:
                draw.text((bubble[0] + 22, y), line, fill=(20, 20, 20), font=font)
                y += 18

        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{spec.order:03d}_{_slug(spec.id)}_r{round_index}.png"
        path = output_dir / filename
        image.save(path)

        return GeneratedAsset(
            spec_id=spec.id,
            path=str(path),
            prompt=spec.prompt,
            seed=seed,
            round_index=round_index,
            metadata={"provider": "mock", "size": [width, height]},
        )
