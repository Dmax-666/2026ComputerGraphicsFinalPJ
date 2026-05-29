# Graphic Agent

Graphic Agent 是一个配置驱动的通用视觉生成 Agent 框架。它的目标不是再做一个固定的 StoryComic 应用，而是提供一套可以被不同场景 YAML 组合的视觉生成工具链。

核心思想：

```text
通用 Python 框架 + 场景 YAML 配置 = 具体视觉生成应用
```

首批场景包括：

- `story_comic`：故事到漫画页生成。
- `game_assets`：游戏设计文档到 2D 素材包生成。

当前版本是 MVP，默认使用 mock provider 离线跑通完整流程，不依赖真实模型 API。后续可以把 LLM、VLM、图像生成模型接入 `tools/` 中的 provider 抽象。

## 为什么不是 StoryComic 专用项目

直接使用多模态模型一次性生成漫画页已经可以得到不错效果。因此项目价值不应停留在“一句话生成一张图”。Graphic Agent 更关注复杂视觉任务中的可控流程：

- 任务规划：根据输入自动拆分视觉资产。
- 风格记忆：为所有资产维护统一 StyleGuide。
- 多工具调用：LLM、VLM、生图模型、排版器、渲染器都以工具形式接入。
- 审稿与重试：视觉审稿器发现问题后，由 revision controller 决定是否局部重试。
- 可解释中间产物：保存 plan、style guide、asset specs、critique report、final image。
- 场景复用：漫画、游戏素材、海报、UI mockup 都可以通过配置加载。

## 快速开始

安装依赖：

```bash
python -m pip install -e ".[dev]"
```

运行故事转漫画 demo：

```bash
graphic-agent run \
  --scenario configs/scenarios/story_comic.yaml \
  --input examples/story_comic_robot_cat.yaml \
  --output outputs/story_comic_robot_cat
```

运行游戏素材 demo：

```bash
graphic-agent run \
  --scenario configs/scenarios/game_assets.yaml \
  --input examples/game_assets_fantasy_rpg.yaml \
  --output outputs/game_assets_fantasy_rpg
```

如果不安装命令行脚本，也可以使用模块方式：

```bash
PYTHONPATH=src python -m graphic_agent.cli run \
  --scenario configs/scenarios/story_comic.yaml \
  --input examples/story_comic_robot_cat.yaml \
  --output outputs/story_comic_robot_cat
```

## 输出结构

每次运行会在输出目录生成：

```text
outputs/<run>/
  assets/
    *.png
  reports/
    task.json
    style_guide.json
    plan.json
    critique_round_1.json
    revision_round_1.json
    result.json
  final.png
```

mock provider 会生成带文字标签的占位图，用于验证 pipeline、配置、渲染和审稿逻辑。真实模型接入后，`assets/*.png` 会替换成模型生成图像。

## 项目结构

```text
configs/
  default.yaml
  providers/
  scenarios/
docs/
examples/
src/graphic_agent/
  agents/
  evaluators/
  renderers/
  tools/
tests/
```

关键模块：

- `config.py`：加载 YAML 配置和输入任务。
- `schemas.py`：统一数据模型，包括 `VisualTask`、`AssetSpec`、`CritiqueReport` 等。
- `pipeline.py`：执行 agentic visual composition loop。
- `agents/`：规划、风格、审稿、修订决策。
- `tools/`：图像生成、存储、未来模型 provider。
- `renderers/`：漫画页、素材表等最终合成器。
- `configs/scenarios/`：不同应用场景的配置。

## 扩展新场景

新场景优先通过 YAML 声明，而不是复制一套新代码。推荐流程：

1. 在 `configs/scenarios/` 新增配置，例如 `poster.yaml`。
2. 声明 `workflow`、`assets`、`render`、`evaluators`、`revision`。
3. 如果已有 renderer 足够，直接复用。
4. 如果需要新输出形式，只新增一个 renderer 并在 registry 中注册。
5. 如果需要新审稿指标，只新增 evaluator 或 critic rule。

原则：

```text
代码提供能力，YAML 组织能力。
```

不要把 YAML 写成复杂 DSL。复杂逻辑应该进入 Python 模块，场景文件只负责组合模块和设置参数。

## 当前状态

- 支持配置加载。
- 支持 `story_comic` 和 `game_assets` 两个场景。
- 支持 mock image generation。
- 支持 Pillow 渲染最终图。
- 支持结构化审稿报告和 revision decision。
- 支持 pytest 基础测试。

下一步是接入真实模型 provider，并让视觉审稿器基于 VLM 输出结构化问题。
