"""Vision provider interface placeholders."""

from pathlib import Path
from typing import Protocol


class VisionReviewTool(Protocol):
    def review_image(self, image_path: Path, rubric: str) -> str:
        """Return a natural-language review for an image and rubric."""
