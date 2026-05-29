# 场景配置说明

## 1. 场景配置的作用

Graphic Agent 使用 `configs/scenarios/*.yaml` 描述不同视觉生成任务。场景文件不应该写复杂逻辑，而是声明：

- 使用什么 workflow。
- 需要哪些 agent。
- 生成哪些资产类型。
- 使用哪种 renderer。
- 审稿指标是什么。
- revision budget 是多少。
- 输出哪些中间产物。

## 2. Story Comic 场景

文件：`configs/scenarios/story_comic.yaml`

目标：输入短故事，输出一页 4 到 8 格漫画。

核心配置：

```yaml
name: story_comic
workflow: visual_composition
assets:
  types:
    - character_reference
    - panel
    - speech_bubble
  default_panel_count: 4
  panel_count_range: [4, 8]
render:
  type: comic_page
revision:
  max_rounds: 3
  quality_threshold: 0.75
evaluators:
  - narrative_consistency
  - character_consistency
  - text_layout_quality
```

Story Comic 的特殊问题：

- 分格节奏：不同情节需要不同格数和格子大小。
- 角色一致性：同一角色跨格不能漂移。
- 叙事连贯性：每格必须推动故事。
- 对白和旁白：文字最好后期渲染，不依赖生图模型画字。
- 跨格交互：后续可以支持角色或气泡越过 panel 边界。

当前 MVP 的 renderer 使用规则网格；后续可以让 LayoutAgent 输出不规则 panel layout。

## 3. Game Assets 场景

文件：`configs/scenarios/game_assets.yaml`

目标：输入游戏设计文档，输出一致风格的 2D 素材表。

核心配置：

```yaml
name: game_assets
workflow: visual_asset_pack
assets:
  categories:
    - characters
    - environments
    - props
    - icons
    - ui_elements
  assets_per_category: 2
render:
  type: asset_sheet
revision:
  max_rounds: 3
  quality_threshold: 0.8
evaluators:
  - style_consistency
  - asset_completeness
  - category_coverage
```

Game Assets 的特殊问题：

- 资产类别要完整。
- 图标、角色、环境、UI 需要风格统一。
- 图像要适合进入游戏原型，而不是只适合展示。
- 后续可以导出 sprite sheet、透明背景 PNG、Godot/Unity metadata。

## 4. 新增场景模板

新增场景可以从下面模板开始：

```yaml
name: my_scenario
description: What this scenario generates.
workflow: visual_composition

models:
  planner:
    provider: mock
    model: mock-planner
  critic:
    provider: mock
    model: mock-vision-critic
  image:
    provider: mock
    model: mock-image-generator

agents:
  - planner
  - style_director
  - image_generator
  - critic
  - revision_controller

assets:
  types:
    - visual_asset

render:
  type: asset_sheet
  page_size: [1600, 1600]
  margin: 64
  gutter: 24
  background: "#ffffff"

revision:
  max_rounds: 2
  retry_budget_per_asset: 1
  quality_threshold: 0.75

evaluators:
  - style_consistency
```

如果已有 planner 和 renderer 无法满足需求，再添加 Python 模块，而不是强行扩展 YAML。
