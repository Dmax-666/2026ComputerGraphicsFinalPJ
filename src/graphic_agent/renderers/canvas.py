"""Shared drawing helpers for Pillow-based renderers."""

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def load_font() -> ImageFont.ImageFont:
    return ImageFont.load_default()


def open_and_fit(
    path: str | Path,
    size: tuple[int, int],
    background: str = "#ffffff",
) -> Image.Image:
    """Open an image and fit it into a fixed box with letterboxing."""

    image = Image.open(path).convert("RGB")
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, background)
    x = (size[0] - image.width) // 2
    y = (size[1] - image.height) // 2
    canvas.paste(image, (x, y))
    return canvas


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    width_chars: int,
    fill: tuple[int, int, int] | str,
    font: ImageFont.ImageFont,
    max_lines: int = 4,
    line_height: int = 18,
) -> None:
    x, y = xy
    lines = textwrap.wrap(text, width=max(8, width_chars))[:max_lines]
    for line in lines:
        draw.text((x, y), line, fill=fill, font=font)
        y += line_height
