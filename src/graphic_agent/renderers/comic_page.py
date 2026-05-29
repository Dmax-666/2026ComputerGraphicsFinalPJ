"""Comic-page renderer for the story_comic scenario."""

from math import ceil
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


class ComicPageRenderer:
    """Compose panel assets into a single comic page."""

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

        title_bar_height = 110
        draw.rectangle((0, 0, width, title_bar_height), fill="#202020")
        draw.text((config.margin, 38), task.title, fill="#ffffff", font=font)

        panel_specs = [spec for spec in specs if spec.type == "panel"]
        if not panel_specs:
            panel_specs = specs
        asset_by_id = {asset.spec_id: asset for asset in generated_assets}

        count = max(1, len(panel_specs))
        columns = 2 if count > 1 else 1
        rows = ceil(count / columns)
        x0 = config.margin
        y0 = title_bar_height + config.margin
        usable_width = width - 2 * config.margin - (columns - 1) * config.gutter
        usable_height = height - y0 - config.margin - (rows - 1) * config.gutter
        cell_width = usable_width // columns
        cell_height = usable_height // rows
        layout: list[dict[str, object]] = []

        for index, spec in enumerate(panel_specs):
            row = index // columns
            col = index % columns
            left = x0 + col * (cell_width + config.gutter)
            top = y0 + row * (cell_height + config.gutter)
            box = (left, top, left + cell_width, top + cell_height)
            asset = asset_by_id.get(spec.id)
            if asset:
                image = open_and_fit(asset.path, (cell_width, cell_height), background="#eeeeee")
                page.paste(image, (left, top))
            else:
                draw.rectangle(box, fill="#dddddd")
            draw.rectangle(box, outline="#111111", width=6)

            dialogue = str(spec.metadata.get("dialogue", ""))
            if dialogue:
                bubble_height = min(92, max(58, cell_height // 4))
                bubble = (
                    left + 24,
                    top + cell_height - bubble_height - 24,
                    left + cell_width - 24,
                    top + cell_height - 24,
                )
                draw.rounded_rectangle(
                    bubble,
                    radius=24,
                    fill="#ffffff",
                    outline="#111111",
                    width=3,
                )
                draw_wrapped_text(
                    draw,
                    dialogue,
                    (bubble[0] + 20, bubble[1] + 18),
                    width_chars=max(18, cell_width // 14),
                    fill="#111111",
                    font=font,
                    max_lines=3,
                )

            layout.append({"asset_id": spec.id, "box": list(box), "type": spec.type})

        output_path = output_dir / "final.png"
        page.save(output_path)
        return CompositionSpec(
            type="comic_page",
            page_size=config.page_size,
            output_path=str(output_path),
            layout=layout,
            metadata={"panel_count": len(panel_specs)},
        )
