from graphic_agent.schemas import (
    AssetSpec,
    ContextMemory,
    CostSummary,
    RenderConfig,
    RevisionDecision,
    StyleGuide,
    VisualTask,
)


def test_render_config_normalizes_page_size() -> None:
    config = RenderConfig(page_size=[1200, 800])
    assert config.page_size == (1200, 800)


def test_asset_spec_normalizes_size() -> None:
    spec = AssetSpec(
        id="asset",
        type="panel",
        category="comic_panel",
        title="Panel",
        description="Description",
        purpose="Purpose",
        prompt="Prompt",
        size=[640, 480],
    )
    assert spec.size == (640, 480)


def test_asset_spec_default_difficulty_and_depends_on() -> None:
    spec = AssetSpec(
        id="a", type="t", category="c", title="T",
        description="d", purpose="p", prompt="pr",
    )
    assert spec.difficulty_estimate == 0.5
    assert spec.depends_on == []


def test_asset_spec_custom_difficulty_and_depends_on() -> None:
    spec = AssetSpec(
        id="panel_1", type="panel", category="comic",
        title="P1", description="d", purpose="p", prompt="pr",
        difficulty_estimate=0.9,
        depends_on=["character_ref"],
    )
    assert spec.difficulty_estimate == 0.9
    assert spec.depends_on == ["character_ref"]


def test_visual_task_from_payload_defaults() -> None:
    task = VisualTask.from_payload({"title": "Demo", "prompt": "Draw a village."})
    assert task.style == {}
    assert task.constraints == {}


def test_style_guide_reference_assets() -> None:
    sg = StyleGuide(
        name="test", visual_style="anime",
        reference_assets={"hero": "/tmp/hero.png"},
    )
    assert sg.reference_assets["hero"] == "/tmp/hero.png"


def test_style_guide_reference_assets_default_empty() -> None:
    sg = StyleGuide(name="test", visual_style="anime")
    assert sg.reference_assets == {}


def test_context_memory_defaults() -> None:
    cm = ContextMemory()
    assert cm.style_patches == []
    assert cm.character_descriptions == {}
    assert cm.reference_image_paths == {}
    assert cm.revision_lessons == []
    assert cm.extra == {}


def test_context_memory_accumulation() -> None:
    cm = ContextMemory()
    cm.revision_lessons.append("lesson 1")
    cm.character_descriptions["hero"] = "tall robot"
    cm.reference_image_paths["hero"] = "/tmp/ref.png"
    assert len(cm.revision_lessons) == 1
    assert cm.character_descriptions["hero"] == "tall robot"


def test_cost_summary_defaults() -> None:
    cs = CostSummary()
    assert cs.total_rounds == 0
    assert cs.total_generation_calls == 0
    assert cs.total_retry_calls == 0
    assert cs.per_asset_calls == {}


def test_revision_decision_prompt_rewrites_and_trace() -> None:
    rd = RevisionDecision(
        action="retry_assets",
        rationale="test",
        retry_asset_ids=["a1"],
        prompt_rewrites={"a1": "new prompt"},
        reasoning_trace=["step 1", "step 2"],
    )
    assert rd.prompt_rewrites["a1"] == "new prompt"
    assert len(rd.reasoning_trace) == 2


def test_revision_decision_defaults() -> None:
    rd = RevisionDecision(action="accept", rationale="ok")
    assert rd.prompt_rewrites == {}
    assert rd.reasoning_trace == []
    assert rd.retry_asset_ids == []
