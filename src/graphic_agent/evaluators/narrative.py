"""Future narrative consistency helpers."""

from graphic_agent.schemas import AssetSpec


def ordered_panel_ids(specs: list[AssetSpec]) -> list[str]:
    return [spec.id for spec in sorted(specs, key=lambda item: item.order) if spec.type == "panel"]
