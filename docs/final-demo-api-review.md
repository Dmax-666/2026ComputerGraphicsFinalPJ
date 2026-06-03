# Final Demo API Profile and Pricing Review

Status: HITL pending

Pricing checked at: 2026-06-03

Parent issue: `docs/issues/api-provider-strategy/006-final-demo-profile-and-pricing-review.md`

## Recommendation

Use `openai_compatible` as the primary final-demo provider profile and `google` or `dashscope` as fallback profiles.

Keep `mock` as the reproducible baseline for tests, CI-style verification, and the presentation fallback. Real-provider outputs should be treated as gallery enhancements, not as the only way to demonstrate Graphic Agent.

## Primary Profile

Primary profile: `configs/providers/openai_compatible.yaml`

Model roles:

- Planner: `gpt-5.4-mini`
- Critic: `gpt-5.4`
- Image generator: `gpt-image-2`

Why:

- It matches the existing OpenAI-compatible tracer path.
- It supports a clear planner / critic / image role split.
- It is the least disruptive path for the current codebase.

Current official pricing notes:

- OpenAI lists `gpt-5.4-mini` at $0.75 / 1M input tokens and $4.50 / 1M output tokens for standard short-context usage.
- OpenAI lists `gpt-5.4` at $2.50 / 1M input tokens and $15.00 / 1M output tokens for standard short-context usage.
- OpenAI lists `gpt-image-2` image input at $8.00 / 1M tokens and output at $30.00 / 1M tokens. Use the image generation guide calculator for exact per-image estimates.

## Fallback Profiles

Fallback profile A: `configs/providers/google.yaml`

- Planner / critic: `gemini-2.5-flash`
- Image generator: Imagen 4 Fast
- Current official pricing notes: Google lists Imagen 4 Fast at $0.02 / image and Imagen 4 Standard at $0.04 / image.

Fallback profile B: `configs/providers/dashscope.yaml`

- Planner: `qwen-plus-2025-12-01`
- Critic: `qwen-vl-plus-2025-08-15`
- Image generator: `qwen-image-plus`
- Current official pricing notes: Alibaba Cloud lists `qwen-image-plus` at $0.03 / image for international deployment and about $0.028671 / image for Chinese mainland deployment.

Text-only low-cost helper: `configs/providers/deepseek.yaml`

- Use `deepseek-v4-flash` for planning or prompt rewrite experiments only.
- Current official pricing notes: DeepSeek lists `deepseek-v4-flash` at $0.14 / 1M cache-miss input tokens and $0.28 / 1M output tokens.
- Do not use deprecated `deepseek-chat` or `deepseek-reasoner` as long-term model IDs.

Text / vision alternative: `configs/providers/anthropic.yaml`

- Anthropic can be used for planner or critic experiments.
- It does not satisfy the image generation role alone.
- Current official pricing notes: Anthropic lists Claude Haiku 4.5 at $1 / 1M input tokens and $5 / 1M output tokens, and Claude Sonnet 4.5 at $3 / 1M input tokens and $15 / 1M output tokens.

## Demo Budget

Baseline asset counts before retries:

- Story Comic: 5 images
- Game Assets: 10 images
- Concept Art Board: 8 images
- Total: 23 images

Use `estimate_run_budget` before any paid run:

```bash
python -m pytest tests/test_costing.py -q
```

Recommended working budget:

- Normal teammate budget: $5-$10
- Comfortable team budget: $20
- Use mock for iteration; spend real API budget only for final gallery assets.

## Human Decisions

- [ ] API key owner confirmed.
- [ ] Primary profile approved.
- [ ] Fallback profile approved.
- [ ] Final scenario outputs selected for real image generation.
- [ ] Real API run date recorded.
- [ ] Generated gallery assets reviewed by the team.
- [ ] Pricing assumptions refreshed again on the final report date.

## Suggested Final Gallery

- [ ] One Story Comic page generated with `openai_compatible`.
- [ ] One Game Assets sheet generated with `openai_compatible` or fallback image provider.
- [ ] One Concept Art Board generated with a low-cost fallback only if budget remains.

## Source Pages

- OpenAI pricing: https://developers.openai.com/api/docs/pricing
- OpenAI image generation guide: https://developers.openai.com/api/docs/guides/image-generation
- Google Gemini pricing: https://ai.google.dev/gemini-api/docs/pricing
- DeepSeek pricing: https://api-docs.deepseek.com/quick_start/pricing
- Anthropic Claude pricing: https://platform.claude.com/docs/en/about-claude/pricing
- Alibaba Cloud Model Studio pricing: https://www.alibabacloud.com/help/en/model-studio/models

