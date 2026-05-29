"""Future style and identity consistency evaluators."""

from graphic_agent.schemas import AssetSpec


def count_categories(specs: list[AssetSpec]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for spec in specs:
        counts[spec.category] = counts.get(spec.category, 0) + 1
    return counts
