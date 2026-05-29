# 技术栈与学习路线

## 1. 当前 MVP 技术栈

当前实现尽量保持轻量：

- Python 3.11+
- Pydantic：结构化 schema 和配置验证。
- PyYAML：读取场景和任务 YAML。
- Pillow：生成 mock 图片和最终合成图。
- Typer：命令行入口。
- Rich：命令行结果展示。
- Pytest：自动化测试。
- Ruff：代码格式和静态检查。

## 2. 为什么使用 Pydantic

Agent 系统最容易失控的地方是中间状态全是自由文本。Pydantic 的作用是把关键状态固定下来：

- planner 必须输出 `AssetSpec[]`。
- critic 必须输出 `CritiqueReport`。
- revision controller 必须输出 `RevisionDecision`。
- pipeline 最终输出 `PipelineResult`。

这样做有利于测试、调试、日志记录和后续接真实模型。

## 3. 为什么使用 YAML

YAML 适合表达场景配置：

- 可读性比 JSON 好。
- 适合手动编辑。
- 可以作为实验配置归档。
- 便于未来批量运行不同场景。

但 YAML 不应该承担复杂逻辑。复杂逻辑应该写在 Python 中。

## 4. 为什么使用 Pillow

Pillow 足够完成 MVP 需要的图像拼接、边框、文字和基础布局。它比完整前端或复杂图形引擎更轻。

后续如果需要更强排版能力，可以考虑：

- OpenCV：检测、裁剪、视觉处理。
- CairoSVG / WeasyPrint：更复杂的文字和矢量排版。
- HTML/CSS renderer：如果需要网页级排版能力。
- Game engine exporter：如果要直接输出 Unity/Godot 资产。

## 5. 后续真实模型接入

建议接入顺序：

1. LLM planner：替换 deterministic planner，输出结构化 `AssetSpec`。
2. Image provider：替换 mock image generator，生成真实图像。
3. VLM critic：替换 mock critic，检查视觉质量。
4. Prompt optimizer：根据 critique 自动改写 prompt。
5. Layout agent：为漫画和海报生成非规则布局。

模型选择应保持 provider 抽象，不要写死某个模型。例如：

```yaml
models:
  planner:
    provider: openai_compatible
    model: gpt-5
  critic:
    provider: openai_compatible
    model: gpt-5-v
  image:
    provider: openai_compatible
    model: gpt-image-2
```

也可以替换成 GLM、FLUX、Kolors 或本地 diffusers provider。

## 6. 建议学习路线

如果这是第一次做 agent 项目，建议按下面顺序学习：

1. Python packaging：`pyproject.toml`、`src/` layout、editable install。
2. Pydantic：BaseModel、字段校验、JSON 序列化。
3. YAML config：配置加载、实验管理。
4. Typer CLI：做可复现命令行工具。
5. Pillow：图像拼接、文字绘制、布局。
6. LLM structured output：让模型输出 JSON/schema。
7. VLM judging：把视觉检查变成结构化报告。
8. Agentic loop：预算、重试、审稿、状态记录。
9. Evaluation：定义人工指标和自动指标。
10. Harness integration：把视觉工具暴露给第三方 agent 系统。
