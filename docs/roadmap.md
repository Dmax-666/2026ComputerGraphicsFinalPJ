# Roadmap

## Milestone 0: Repository Skeleton

状态：已完成。

目标：

- 初始化 Python 项目结构。
- 建立 `graphic_agent` 通用包。
- 添加配置、示例、文档和测试。
- 离线 mock provider 能跑通完整流程。

## Milestone 1: Real Provider Interface

目标：

- 实现 OpenAI-compatible text provider。
- 实现 OpenAI-compatible image provider。
- 实现 OpenAI-compatible vision provider。
- 增加 `.env` 加载和 provider config merge。
- 保留 mock provider 作为测试后端。

验收标准：

- 不改 pipeline，只改 provider 配置即可切换 mock 和真实模型。
- LLM 输出经过 Pydantic 校验。
- provider 错误能写入 report。

## Milestone 2: Story Comic Advanced Demo

目标：

- LLM 生成 4 到 8 格分镜。
- 角色 reference image 进入后续 panel prompt。
- LayoutAgent 支持非规则分格。
- 对白和旁白后期排版。
- VLM 检查角色一致性和叙事连贯性。

验收标准：

- 输出完整一页漫画。
- 保存每格 prompt、图像、审稿意见和重试记录。
- 至少支持 3 种风格配置。

## Milestone 3: Game Asset Pack Demo

目标：

- 从游戏设计文档拆分资产清单。
- 输出角色、环境、道具、图标、UI 元素。
- 支持 style reference。
- 支持 asset sheet 和单独 PNG 导出。

验收标准：

- 资产类别覆盖完整。
- 资产风格一致。
- 输出结构适合进入游戏原型。

## Milestone 4: Adaptive Reasoning

目标：

- 让 agent 根据任务难度动态选择多想几轮或多生成几张。
- 为每个资产设置 retry budget。
- 引入 critique-driven prompt rewriting。
- 记录每轮 reasoning 和质量变化。

验收标准：

- 简单任务低成本完成。
- 困难任务自动增加审稿和重试。
- 产物质量变化可以从日志中复盘。

## Milestone 5: Evaluation and Paper-Ready Report

目标：

- 建立人工评价表。
- 建立自动指标：资产覆盖、布局占用、文本遮挡、风格一致性。
- 与 one-shot baseline 对比。
- 整理 demo gallery 和实验报告。

验收标准：

- 有可复现实验配置。
- 有定量和定性分析。
- 能说明 agentic loop 的价值。
