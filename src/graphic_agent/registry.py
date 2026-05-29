"""Small registries for pluggable framework components."""

from graphic_agent.renderers.asset_sheet import AssetSheetRenderer
from graphic_agent.renderers.comic_page import ComicPageRenderer


def get_renderer(render_type: str):
    """Return a renderer instance for the configured render type."""

    renderers = {
        "asset_sheet": AssetSheetRenderer,
        "comic_page": ComicPageRenderer,
    }
    try:
        return renderers[render_type]()
    except KeyError as exc:
        available = ", ".join(sorted(renderers))
        message = f"Unknown renderer '{render_type}'. Available renderers: {available}"
        raise ValueError(message) from exc
