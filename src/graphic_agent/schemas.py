"""Shared data models used by the visual generation pipeline."""

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SUPPORTED_PROVIDERS = {
    "mock",
    "openai_compatible",
    "google",
    "dashscope",
    "deepseek",
    "anthropic",
}


class ModelSpec(BaseModel):
    """Model routing information for one logical model role."""

    provider: str = "mock"
    model: str = "mock"
    parameters: dict[str, Any] = Field(default_factory=dict)

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        if value not in SUPPORTED_PROVIDERS:
            available = ", ".join(sorted(SUPPORTED_PROVIDERS))
            raise ValueError(f"Unknown provider '{value}'. Available providers: {available}")
        return value

    @field_validator("model")
    @classmethod
    def validate_model_version(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("ModelSpec requires a non-empty model version.")
        return value


class ProviderProfile(BaseModel):
    """Provider and model-role settings for one API usage profile."""

    model_config = ConfigDict(extra="allow")

    name: str
    description: str = ""
    env: dict[str, str] = Field(default_factory=dict)
    models: dict[str, ModelSpec] = Field(default_factory=dict)
    pricing: dict[str, Any] = Field(default_factory=dict)
    caveats: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_model_roles(self) -> "ProviderProfile":
        if not self.models:
            raise ValueError("ProviderProfile requires at least one model role mapping.")
        return self


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
    reference_assets: dict[str, str] = Field(default_factory=dict)
    """Mapping of role (e.g. 'protagonist') -> asset path for character /
    style reference images.  Populated after reference assets are generated
    so downstream panels can use them for consistency."""


class ContextMemory(BaseModel):
    """Shared mutable context that accumulates across the pipeline run.

    Acts as a blackboard: agents and evaluators can read from it, and the
    pipeline updates it after each revision round.  This lets downstream
    asset generation benefit from lessons learned earlier in the loop.
    """

    style_patches: list[str] = Field(default_factory=list)
    """Incremental style corrections discovered during revision rounds,
    e.g. 'character hair should be blue, not purple'."""
    character_descriptions: dict[str, str] = Field(default_factory=dict)
    """Canonical text descriptions of key characters, updated as the
    pipeline refines its understanding of visual identity."""
    reference_image_paths: dict[str, str] = Field(default_factory=dict)
    """Paths to generated reference images keyed by role name."""
    revision_lessons: list[str] = Field(default_factory=list)
    """High-level lessons from past revision rounds that should inform
    all future asset generation (e.g. 'avoid cluttered backgrounds')."""
    extra: dict[str, Any] = Field(default_factory=dict)
    """Scenario-specific memory entries not covered above."""


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
    difficulty_estimate: float = 0.5
    """Estimated generation difficulty from 0 (trivial) to 1 (very hard).
    Used by adaptive reasoning to allocate retry budget per asset."""
    depends_on: list[str] = Field(default_factory=list)
    """IDs of assets that must be generated before this one.
    Used to build a dependency DAG for parallel generation."""
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
    prompt_rewrites: dict[str, str] = Field(default_factory=dict)
    """Mapping of asset_id -> rewritten prompt for the next retry round.
    Based on critique recommendations to improve generation quality."""
    reasoning_trace: list[str] = Field(default_factory=list)
    """Step-by-step reasoning that led to this decision.
    Captures why specific assets were retried and what the controller
    expects to improve on the next round."""



class CostSummary(BaseModel):
    """Tracks compute cost across the pipeline run.

    Mock providers populate generation counts; real providers should add
    token counts and API cost estimates so adaptive reasoning can measure
    whether difficulty-aware budgeting actually saves resources.
    """

    total_rounds: int = 0
    total_generation_calls: int = 0
    total_retry_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_image_generations: int = 0
    total_vision_calls: int = 0
    estimated_cost_usd: float = 0.0
    per_asset_calls: dict[str, int] = Field(default_factory=dict)
    """How many generation attempts each asset required (asset_id -> count)."""


class PipelineResult(BaseModel):
    """Serializable result of one full pipeline run."""

    scenario: str
    task: VisualTask
    style_guide: StyleGuide
    context_memory: ContextMemory = Field(default_factory=ContextMemory)
    cost_summary: CostSummary = Field(default_factory=CostSummary)
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
