from graphic_agent.schemas import AssetSpec, RenderConfig, VisualTask


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


def test_visual_task_from_payload_defaults() -> None:
    task = VisualTask.from_payload({"title": "Demo", "prompt": "Draw a village."})
    assert task.style == {}
    assert task.constraints == {}
