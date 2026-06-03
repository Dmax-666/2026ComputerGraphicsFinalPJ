"""Image sanity evaluators that use only Pillow — no external models needed."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from graphic_agent.schemas import (
    AssetSpec,
    CompositionSpec,
    CritiqueIssue,
    GeneratedAsset,
    ScenarioConfig,
)


class ImageSizeEvaluator:
    """Check that each generated image matches the size declared in its AssetSpec."""

    name = "image_size"

    def evaluate(
        self,
        scenario: ScenarioConfig,
        specs: list[AssetSpec],
        generated_assets: list[GeneratedAsset],
        composition: CompositionSpec,
    ) -> list[CritiqueIssue]:
        issues: list[CritiqueIssue] = []
        specs_by_id = {s.id: s for s in specs}

        for asset in generated_assets:
            spec = specs_by_id.get(asset.spec_id)
            if spec is None or not Path(asset.path).exists():
                continue
            try:
                with Image.open(asset.path) as img:
                    actual = img.size  # (width, height)
            except Exception:
                issues.append(
                    CritiqueIssue(
                        asset_id=asset.spec_id,
                        severity="high",
                        category="image_corrupt",
                        message=f"Cannot open image file: {asset.path}",
                        recommendation="Regenerate this asset — file may be corrupt.",
                    )
                )
                continue

            expected = spec.size
            if actual != expected:
                issues.append(
                    CritiqueIssue(
                        asset_id=asset.spec_id,
                        severity="medium",
                        category="image_size_mismatch",
                        message=(
                            f"Expected {expected[0]}x{expected[1]} but got "
                            f"{actual[0]}x{actual[1]}."
                        ),
                        recommendation=(
                            f"Regenerate at the correct resolution ({expected[0]}x{expected[1]})."
                        ),
                    )
                )
        return issues


class FileSanityEvaluator:
    """Detect suspiciously small or empty image files."""

    name = "file_sanity"

    MIN_FILE_BYTES = 512  # A valid PNG with any content is at least ~100 bytes

    def evaluate(
        self,
        scenario: ScenarioConfig,
        specs: list[AssetSpec],
        generated_assets: list[GeneratedAsset],
        composition: CompositionSpec,
    ) -> list[CritiqueIssue]:
        issues: list[CritiqueIssue] = []

        for asset in generated_assets:
            path = Path(asset.path)
            if not path.exists():
                continue
            size_bytes = path.stat().st_size
            if size_bytes < self.MIN_FILE_BYTES:
                issues.append(
                    CritiqueIssue(
                        asset_id=asset.spec_id,
                        severity="high",
                        category="file_too_small",
                        message=(
                            f"Image file is only {size_bytes} bytes — likely corrupt or empty."
                        ),
                        recommendation="Regenerate this asset.",
                    )
                )
        return issues
