# 架构设计

## 1. 总览

Graphic Agent 的架构分为三层：

```text
Scenario Layer: YAML 场景配置
Workflow Layer: Python pipeline 和 agentic loop
Tool Layer: LLM / VLM / image generation / renderer / storage
```

场景层声明“要做什么”，工作流层决定“如何执行”，工具层提供“具体能力”。

## 2. 数据流

当前 MVP 的数据流如下：

```text
Task YAML
  -> VisualTask
Scenario YAML
  -> ScenarioConfig
VisualTask + ScenarioConfig
  -> StyleGuide
  -> AssetSpec[]
  -> GeneratedAsset[]
  -> CompositionSpec
  -> CritiqueReport
  -> RevisionDecision
  -> PipelineResult
```

所有关键中间产物都会保存到 `outputs/<run>/reports/`，便于调试、展示和后续评估。

## 3. 核心抽象

### VisualTask

用户输入任务。它只关心“用户想要什么”，不关心具体生成步骤。

主要字段：

- `title`：任务标题。
- `prompt`：自然语言需求。
- `style`：风格偏好。
- `constraints`：场景约束，例如 panel count、避免内容、资产包规模。

### ScenarioConfig

场景配置。它声明当前任务使用什么 workflow、agent、renderer、evaluator 和 revision 预算。

### StyleGuide

全局风格记忆。它在多资产任务中非常重要，用于减少跨图风格漂移。

### AssetSpec

计划生成的视觉资产。漫画场景里的 panel、游戏场景里的 prop、海报场景里的 title block 都可以被抽象成 `AssetSpec`。

### GeneratedAsset

实际生成出来的图像文件和生成元数据。

### CompositionSpec

最终合成图的布局描述和输出路径。

### CritiqueReport

审稿器输出的结构化问题列表，包括问题类别、严重程度、建议和关联资产。

### RevisionDecision

修订控制器根据审稿结果决定接受、重试部分资产或停止。

## 4. Agentic Loop

当前 pipeline 使用以下循环：

```text
plan assets
generate assets
render composition
critique result
if passed:
    accept
elif budget remains:
    retry failed assets
else:
    stop with best result
```

这和一次性生图的区别是：失败不再只能整体重试，而是可以定位到具体资产或具体质量指标。

## 5. 代码模块

```text
src/graphic_agent/
  cli.py
  config.py
  pipeline.py
  registry.py
  schemas.py
  agents/
  tools/
  renderers/
  evaluators/
```

模块职责：

- `cli.py`：命令行入口。
- `config.py`：加载 YAML。
- `schemas.py`：定义结构化数据模型。
- `pipeline.py`：串联完整工作流。
- `registry.py`：选择 renderer 等可插拔组件。
- `agents/planner.py`：把任务拆成资产计划。
- `agents/style_director.py`：生成统一风格记忆。
- `agents/critic.py`：结构化审稿。
- `agents/revision.py`：根据审稿结果决定下一步。
- `tools/image_gen.py`：图像生成工具，当前为 mock provider。
- `renderers/`：最终图像合成。
- `evaluators/`：未来用于更细粒度质量指标。

## 6. 配置边界

YAML 只负责组合能力，不负责实现复杂逻辑。

推荐边界：

- YAML 中写场景名称、资产类型、渲染参数、阈值和模型选择。
- Python 中写规划策略、审稿规则、渲染算法和模型 provider。

避免把 YAML 变成一门复杂 DSL。否则后续维护会变得困难。

## 7. 真实模型接入方式

未来可以扩展以下工具：

- `TextGenerationTool`：接 LLM，用于规划和 prompt writing。
- `VisionReviewTool`：接 VLM，用于审稿。
- `ImageGenerator`：接 image model，用于图像生成。

建议 provider 都返回结构化对象，而不是直接把字符串传到下一步。这样 pipeline 更稳定，也更容易测试。

## 8. 第三方 Harness 集成

如果要接 OpenCode SDK 或其他 agent harness，Graphic Agent 可以作为工具层暴露：

- `run_scenario(scenario_yaml, input_yaml, output_dir)`
- `plan_assets(task, scenario)`
- `generate_asset(asset_spec, style_guide)`
- `critique_composition(image_path, rubric)`
- `render_composition(asset_paths, render_config)`

第三方 harness 负责更高层推理和任务分配，本项目负责视觉生成工具链和产物管理。
