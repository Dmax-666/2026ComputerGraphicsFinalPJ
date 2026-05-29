"""Shared data models used by the visual generation pipeline."""

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ModelSpec(BaseModel):
    """Model routing information for one logical model role."""

    provider: str = "mock"
    model: str = "mock"
    parameters: dict[str, Any] = Field(default_factory=dict)


class RenderConfig(BaseModel):
    """Renderer settings declared by a scenario file."""

    model_config = ConfigDict(extra="allow")

    type: str = "asset_sheet"
    page_size: tuple[int, int] = (1600, 1600)
    margin: int = 64
    gutter: int = 24
    background: str = "#ffffff"
    text_rendering: str = "postprocess"

    @field_validator("page_size", mode="before")
    @classmethod
    def normalize_page_size(cls, value: Any) -> tuple[int, int]:
        if isinstance(value, list):
            return (int(value[0]), int(value[1]))
        return value


class RevisionConfig(BaseModel):
    """Budget and quality gate for the agentic revision loop."""

    max_rounds: int = 1
    retry_budget_per_asset: int = 0
    quality_threshold: float = 0.75


class ScenarioConfig(BaseModel):
    """Top-level configuration for a visual generation scenario."""

    model_config = ConfigDict(extra="allow")

    name: str
    description: str = ""
    workflow: str = "visual_composition"
    models: dict[str, ModelSpec] = Field(default_factory=dict)
    agents: list[str] = Field(default_factory=list)
    assets: dict[str, Any] = Field(default_factory=dict)
    render: RenderConfig = Field(default_factory=RenderConfig)
    revision: RevisionConfig = Field(default_factory=RevisionConfig)
    evaluators: list[str] = Field(default_factory=list)
    outputs: dict[str, Any] = Field(default_factory=dict)


class VisualTask(BaseModel):
    """User request after loading an example or runtime input file."""

    title: str
    prompt: str
    style: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "VisualTask":
        return cls(**payload)


class StyleGuide(BaseModel):
    """Reusable style memory shared by all generated assets."""

    name: str
    visual_style: str
    palette: list[str] = Field(default_factory=list)
    mood: str = "balanced"
    typography: str = "clear sans-serif labels"
    negative_prompt: str = ""
    notes: list[str] = Field(default_factory=list)


class AssetSpec(BaseModel):
    """A planned visual asset before image generation."""

    id: str
    type: str
    category: str
    title: str
    description: str
    purpose: str
    prompt: str
    order: int = 0
    size: tuple[int, int] = (768, 768)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("size", mode="before")
    @classmethod
    def normalize_size(cls, value: Any) -> tuple[int, int]:
        if isinstance(value, list):
            return (int(value[0]), int(value[1]))
        return value


class GeneratedAsset(BaseModel):
    """Generated image and the generation metadata attached to it."""

    spec_id: str
    path: str
    prompt: str
    seed: int
    status: Literal["generated", "failed"] = "generated"
    round_index: int = 1
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompositionSpec(BaseModel):
    """Final visual composition produced by a renderer."""

    type: str
    page_size: tuple[int, int]
    output_path: str
    layout: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CritiqueIssue(BaseModel):
    """One structured problem found by a critic or evaluator."""

    asset_id: str | None = None
    severity: Literal["low", "medium", "high"] = "low"
    category: str
    message: str
    recommendation: str


class CritiqueReport(BaseModel):
    """Structured quality report after one revision round."""

    score: float
    passed: bool
    summary: str
    issues: list[CritiqueIssue] = Field(default_factory=list)
    evaluator_names: list[str] = Field(default_factory=list)


class RevisionDecision(BaseModel):
    """Controller decision after reading a critique report."""

    action: Literal["accept", "retry_assets", "stop"]
    rationale: str
    retry_asset_ids: list[str] = Field(default_factory=list)


class PipelineResult(BaseModel):
    """Serializable result of one full pipeline run."""

    scenario: str
    task: VisualTask
    style_guide: StyleGuide
    planned_assets: list[AssetSpec]
    generated_assets: list[GeneratedAsset]
    composition: CompositionSpec
    critique: CritiqueReport
    revision: RevisionDecision
    output_dir: str
    final_image: str
    rounds_completed: int


def model_to_jsonable(model: BaseModel) -> dict[str, Any]:
    """Return a JSON-safe dictionary from a pydantic model."""

    return model.model_dump(mode="json")


def path_to_str(path: Path | str) -> str:
    return str(Path(path))
