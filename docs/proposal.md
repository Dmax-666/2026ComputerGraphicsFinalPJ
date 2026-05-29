# 项目方案：Graphic Agent

## 1. 项目定位

Graphic Agent 是一个配置驱动的通用视觉生成 Agent 框架。它不是固定的 StoryComic 应用，而是一个可以通过 YAML 场景文件加载不同视觉任务的 agentic harness。

核心公式：

```text
通用框架 + 场景配置 + 模型工具 = 具体视觉生成应用
```

第一阶段选择两个代表性场景：

- 故事转漫画：输入短故事，输出一页多格漫画。
- 游戏素材生成：输入游戏设计文档，输出一致风格的 2D 素材包。

这两个场景都不是简单的一次性文生图任务。它们都需要全局风格记忆、资产拆分、布局组合、视觉审稿和局部重试。

## 2. 背景与动机

现有视觉生成模型已经可以直接生成海报、漫画页和游戏概念图。例如，把一个故事 prompt 直接交给图像模型，有时也能得到不错结果。但 one-shot 生成存在几个问题：

- 过程不可解释：用户看不到模型如何拆分任务。
- 失败不可定位：如果图像失败，只能整体重试。
- 一致性不稳定：角色、风格、UI 语言在多张图之间容易漂移。
- 文本和布局难控：漫画对白、UI 文案、海报文字经常不可靠。
- 难以扩展：每个应用都需要重新写一套 prompt 和处理逻辑。

Graphic Agent 的目标是把视觉生成任务拆成可观察、可审稿、可重试的流程。

## 3. 与相关工作的区别

Paper2Poster、PosterForest 等工作关注论文到海报的内容筛选和版面布局。它们的主要挑战是信息压缩、模块排列和可读性。

漫画和游戏素材生成的挑战不同：

- 漫画需要叙事节奏、分格顺序、跨格角色一致性和对白气泡定位。
- 游戏素材需要成套资产、风格统一、类别覆盖和可直接进入原型流程。
- 多场景视觉生成需要工具编排，而不是一个固定模板。

商业工具通常重视最终效果，但很少开放中间表示、审稿过程和可插拔 agent loop。Graphic Agent 的价值在于开源、配置化、可解释和可扩展。

## 4. 核心研究问题

本项目可以围绕以下问题展开：

1. 在复杂视觉生成任务中，agentic loop 是否能比 one-shot 生成提供更好的可控性？
2. 结构化中间表示能否降低多场景视觉生成系统的开发成本？
3. VLM 审稿和局部重试能否提升角色一致性、风格一致性和布局质量？
4. YAML 配置驱动的任务编排是否适合作为第三方 harness 的视觉工具层？

## 5. 技术路线

第一版采用离线 mock provider 跑通完整 pipeline：

```text
input YAML
  -> scenario config
  -> style guide
  -> asset plan
  -> mock image generation
  -> renderer composition
  -> mock critic
  -> revision decision
  -> final artifacts
```

后续把 mock provider 替换成真实模型：

- LLM：负责任务规划、分镜、资产拆分、prompt 写作。
- Image model：负责角色图、分格图、游戏资产图生成。
- VLM：负责视觉审稿、角色一致性检查、布局遮挡检查。
- Renderer：负责后期排版、文字渲染、资产表导出。

## 6. 预期贡献

项目可以形成以下贡献：

- 一个开源的 agentic visual generation framework。
- 一套通用结构化 schema：`VisualTask`、`StyleGuide`、`AssetSpec`、`CritiqueReport`。
- 两个可运行示例场景：Story Comic 和 Game Assets。
- 一个可复用的 revision loop：审稿、定位问题、局部重试。
- 一个面向后续模型接入和 OpenCode/第三方 harness 的工具层设计。

## 7. 阶段目标

MVP 阶段的成功标准：

- 能通过 YAML 加载不同场景。
- 能在无 API key 环境下跑通完整流程。
- 能保存中间 JSON 和最终图像。
- 能通过测试验证核心 schema、配置和 pipeline。
- 文档能清晰说明如何扩展新场景和接入真实模型。
