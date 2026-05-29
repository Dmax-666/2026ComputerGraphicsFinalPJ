"""Asset-sheet renderer for game asset scenarios."""

from math import ceil, sqrt
from pathlib import Path

from PIL import Image, ImageDraw

from graphic_agent.renderers.canvas import draw_wrapped_text, load_font, open_and_fit
from graphic_agent.schemas import (
    AssetSpec,
    CompositionSpec,
    GeneratedAsset,
    RenderConfig,
    VisualTask,
)


class AssetSheetRenderer:
    """Compose generated assets into a labeled contact sheet."""

    def render(
        self,
        task: VisualTask,
        specs: list[AssetSpec],
        generated_assets: list[GeneratedAsset],
        config: RenderConfig,
        output_dir: Path,
    ) -> CompositionSpec:
        width, height = config.page_size
        page = Image.new("RGB", (width, height), config.background)
        draw = ImageDraw.Draw(page)
        font = load_font()
        asset_by_id = {asset.spec_id: asset for asset in generated_assets}

        draw.text((config.margin, 36), task.title, fill="#ffffff", font=font)
        draw_wrapped_text(
            draw,
            task.prompt,
            (config.margin, 68),
            width_chars=120,
            fill="#d8dee9",
            font=font,
            max_lines=2,
        )

        count = max(1, len(specs))
        columns = max(1, ceil(sqrt(count)))
        rows = ceil(count / columns)
        top_offset = 130
        usable_width = width - 2 * config.margin - (columns - 1) * config.gutter
        usable_height = height - top_offset - config.margin - (rows - 1) * config.gutter
        cell_width = usable_width // columns
        cell_height = usable_height // rows
        image_height = max(100, cell_height - 58)
        layout: list[dict[str, object]] = []

        for index, spec in enumerate(specs):
            row = index // columns
            col = index % columns
            left = config.margin + col * (cell_width + config.gutter)
            top = top_offset + row * (cell_height + config.gutter)
            box = (left, top, left + cell_width, top + cell_height)
            draw.rounded_rectangle(
                box,
                radius=20,
                fill="#1d2b36",
                outline="#d8dee9",
                width=2,
            )

            asset = asset_by_id.get(spec.id)
            image_box = (cell_width - 28, image_height)
            if asset:
                image = open_and_fit(asset.path, image_box, background="#283845")
                page.paste(image, (left + 14, top + 14))
            draw.text(
                (left + 18, top + image_height + 24),
                spec.title[:48],
                fill="#ffffff",
                font=font,
            )
            draw.text(
                (left + 18, top + image_height + 44),
                spec.category,
                fill="#a6e3a1",
                font=font,
            )
            layout.append({"asset_id": spec.id, "box": list(box), "type": spec.type})

        output_path = output_dir / "final.png"
        page.save(output_path)
        return CompositionSpec(
            type="asset_sheet",
            page_size=config.page_size,
            output_path=str(output_path),
            layout=layout,
            metadata={"asset_count": len(specs)},
        )
