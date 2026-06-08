# Graphic Agent

Graphic Agent 是一个配置驱动的通用视觉生成 Agent 框架。它不是单一的漫画或海报生成脚本，而是把“任务理解、资产规划、风格记忆、Prompt 优化、图像生成、排版合成、审稿、修订重试”拆成一条可审计的视觉生成流水线。

核心思想：

```text
通用 Python 框架 + 场景 YAML 配置 + 可切换 provider = 具体视觉生成应用
```

当前项目支持离线 mock demo，也支持双 API full-agent demo：

```text
文本 / 视觉 API：StyleGuide、Planner、Prompt Refinement、Critic、Revision
图像 API：根据结构化 AssetSpec 生成视觉资产
本地 Python：流程控制、文件保存、成本记录、最终排版合成
```

## 三个 YAML 场景

项目内置三个场景配置，位于 `configs/scenarios/`。它们定义“任务如何拆分、生成什么资产、如何合成、如何审稿、最多重试几轮”。

### `story_comic.yaml`

故事转一页漫画。

```text
输入短故事
-> 生成 StyleGuide
-> 规划角色参考图和 4 到 8 个漫画 panel
-> 生成每个 panel
-> 合成一页漫画 final.png
-> 检查叙事、角色一致性、文字排版、图片尺寸、文件有效性
-> 必要时局部重画 panel
```

示例输入：

```text
examples/story_comic_robot_cat.yaml
```

当前示例讲的是：一个小型送货机器人在雨夜霓虹城市里寻找走丢的小猫。

### `game_assets.yaml`

游戏设定文档转 2D 素材包。

```text
输入游戏世界观 / 设计文档
-> 按类别规划素材
-> 生成 characters、environments、props、icons、ui_elements
-> 每类默认 2 个素材，共 10 个资产
-> 合成一张 asset sheet
-> 检查风格一致性、类别覆盖、素材完整性、尺寸、文件有效性
-> 必要时只重画有问题的资产
```

示例输入：

```text
examples/game_assets_fantasy_rpg.yaml
```

这个场景适合展示“同一套视觉风格下的游戏原型素材包”。

### `concept_art_board.yaml`

概念设定探索板。

```text
输入一个概念主题
-> 对 character 和 environment 两类主题做设计探索
-> 每类生成 4 个视觉变体，共 8 个资产
-> 合成一张 concept art board
-> 检查风格一致性、尺寸、文件有效性
-> 必要时重画质量不足的变体
```

示例输入：

```text
examples/concept_art_cyberpunk_hero.yaml
```

这个场景适合展示“同一主题下的多方向视觉探索”。

## Full-Agent 流程

真实 provider 运行时，pipeline 会按以下顺序工作：

```text
Task YAML
  -> Text API 生成 StyleGuide
  -> Text API 规划 AssetSpec 列表
  -> Text API 优化每个生图 prompt
  -> Image API 生成 assets/*.png
  -> 本地 renderer 合成 final.png
  -> Text/Vision API 审稿 final.png
  -> Text API 决定 accept / retry_assets / stop
  -> Image API 局部重画需要重试的资产
```

如果文本 API 支持图片输入，critic 会把 `final.png` 作为图片发给模型做 VLM 审稿。如果网关不支持图片输入，critic 会降级为基于结构化报告和资产元数据的文本审稿；如果外部审稿失败，则保留本地 evaluator 结果作为兜底。

## 快速开始

安装依赖：

```bash
python -m pip install -e ".[dev]"
```

如果不安装命令行脚本，也可以使用模块方式运行。Windows PowerShell 示例：

```powershell
$env:PYTHONPATH="src"
python -m graphic_agent.cli --help
```

## 离线 Mock 运行

mock 模式不需要 API key，会生成带文字标签的占位图，用于验证 pipeline、报告结构和排版逻辑。

```powershell
$env:PYTHONPATH="src"

python -m graphic_agent.cli run `
  --scenario configs/scenarios/story_comic.yaml `
  --input examples/story_comic_robot_cat.yaml `
  --output outputs/story_comic_mock
```

## 双 API 真实运行

真实运行使用 `configs/providers/openai_compatible.yaml`。当前配置支持把文本模型和图像模型放在不同 API 网关上。

环境变量：

```powershell
$env:PYTHONPATH="src"

$env:OPENAI_API_KEY="你的生图 API key"
$env:OPENAI_BASE_URL="https://api.aipaibox.com/v1"

$env:OPENAI_TEXT_API_KEY="你的文本 / 视觉 API key"
$env:OPENAI_TEXT_BASE_URL="https://aigw.sotatts.online/v1"
```

先检查环境：

```powershell
python -m graphic_agent.cli provider-check `
  --provider-profile configs/providers/openai_compatible.yaml
```

运行三个场景：

```powershell
python -m graphic_agent.cli run `
  --scenario configs/scenarios/story_comic.yaml `
  --input examples/story_comic_robot_cat.yaml `
  --output outputs/story_comic_full_agent `
  --provider-profile configs/providers/openai_compatible.yaml
```

```powershell
python -m graphic_agent.cli run `
  --scenario configs/scenarios/game_assets.yaml `
  --input examples/game_assets_fantasy_rpg.yaml `
  --output outputs/game_assets_full_agent `
  --provider-profile configs/providers/openai_compatible.yaml
```

```powershell
python -m graphic_agent.cli run `
  --scenario configs/scenarios/concept_art_board.yaml `
  --input examples/concept_art_cyberpunk_hero.yaml `
  --output outputs/concept_art_full_agent `
  --provider-profile configs/providers/openai_compatible.yaml
```

注意：真实图像 API 调用较慢，且 revision 可能触发额外生图。`story_comic` 初始 5 张图，`game_assets` 初始 10 张图，`concept_art_board` 初始 8 张图。

## 成本估算

单场景估算：

```powershell
python -m graphic_agent.cli estimate `
  --scenario configs/scenarios/story_comic.yaml `
  --input examples/story_comic_robot_cat.yaml `
  --provider-profile configs/providers/openai_compatible.yaml
```

三个 demo 一起估算：

```powershell
python -m graphic_agent.cli estimate-suite `
  --suite configs/demo_suite.yaml `
  --provider-profile configs/providers/openai_compatible.yaml
```

## 输出结构

每次运行会在输出目录生成：

```text
outputs/<run>/
  assets/
    *_r1_openai.png
    *_r2_openai.png
  reports/
    task.json
    style_generation.json
    style_guide.json
    planning.json
    plan.json
    prompt_refinement.json
    critique_round_1.json
    critic_llm_round_1.json
    revision_round_1.json
    revision_llm_round_1.json
    context_memory.json
    cost_summary.json
    result.json
  final.png
```

关键报告：

- `style_generation.json`：文本 API 生成风格记忆的过程和兜底状态。
- `planning.json`：文本 API 规划资产的过程和资产数量。
- `plan.json`：最终用于生图的结构化 `AssetSpec` 列表。
- `prompt_refinement.json`：文本 API 对每个生图 prompt 的优化结果。
- `critic_llm_round_<n>.json`：每轮 LLM/VLM 审稿状态。
- `revision_llm_round_<n>.json`：每轮 LLM revision 决策。
- `cost_summary.json`：文本 token、图片生成次数、重试次数、估算成本。
- `result.json`：整次运行的最终结构化结果。

`assets/*_r1_openai.png` 是第一轮图像。如果审稿触发局部重试，会出现 `*_r2_openai.png` 或更高轮次文件。最终 `final.png` 使用的是每个资产的最新通过版本。

## 项目结构

```text
configs/
  default.yaml
  demo_suite.yaml
  providers/
    mock.yaml
    openai_compatible.yaml
    google.yaml
    dashscope.yaml
    deepseek.yaml
    anthropic.yaml
  scenarios/
    story_comic.yaml
    game_assets.yaml
    concept_art_board.yaml
docs/
examples/
outputs/
src/graphic_agent/
  agents/
  evaluators/
  renderers/
  tools/
tests/
```

关键模块：

- `config.py`：加载 YAML 场景、输入任务和 provider profile。
- `schemas.py`：统一数据模型，包括 `VisualTask`、`StyleGuide`、`AssetSpec`、`CritiqueReport`、`RevisionDecision`、`CostSummary`。
- `pipeline.py`：串联 full-agent visual generation loop。
- `agents/`：风格生成、规划、prompt refinement、审稿、修订控制。
- `tools/openai_compatible.py`：OpenAI-compatible 文本和图像 provider。
- `renderers/`：漫画页和素材展示板合成器。
- `evaluators/`：本地兜底审稿规则。

## 扩展新场景

新场景优先通过 YAML 声明，而不是复制一套新代码。

推荐流程：

1. 在 `configs/scenarios/` 新增配置，例如 `poster.yaml`。
2. 声明 `workflow`、`assets`、`render`、`evaluators`、`revision`。
3. 如果已有 renderer 足够，直接复用。
4. 如果需要新输出形式，新增 renderer 并在 registry 中注册。
5. 如果需要新审稿指标，新增 evaluator 或扩展 LLM critic rubric。

原则：

```text
代码提供能力，YAML 组织能力。
```

不要把 YAML 写成复杂 DSL。复杂逻辑应该进入 Python 模块，场景文件只负责组合模块和设置参数。

## 当前状态

- 支持离线 mock provider。
- 支持 OpenAI-compatible 文本 API 和图像 API。
- 支持双 API full-agent loop。
- 支持三个场景：`story_comic`、`game_assets`、`concept_art_board`。
- 支持 Pillow 最终合成。
- 支持 LLM/VLM 审稿、revision prompt rewrite 和局部重试。
- 支持结构化中间报告和成本统计。
- 支持 pytest 测试。
