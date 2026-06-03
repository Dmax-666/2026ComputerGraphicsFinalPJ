# PRD: API Provider Strategy and Cost Controls

## Problem Statement

Graphic Agent is positioned as a configurable, auditable visual generation orchestrator. The current MVP can run with mock providers, but the final project also needs a credible path for optional real-model demos. Without a clear API provider strategy, the team risks choosing unstable model versions, overspending on image generation, leaking API keys, or making the demo depend on a provider that is unavailable during presentation.

The team needs a product-level decision document that defines which suppliers and model versions should be used for each model role, how costs should be estimated before a run, how actual usage should be recorded after a run, and how the project can remain reproducible when no paid API key is available.

## Solution

Add an API provider strategy for Graphic Agent that keeps mock providers as the default execution path and treats real APIs as optional demo enhancements.

The strategy assigns model roles rather than hardcoding one universal model:

- Planner and prompt rewrite use a low-cost structured-output LLM.
- Critic uses a stronger multimodal model only when visual review is needed.
- Image generator uses a dedicated image model, with draft and final quality modes.

The recommended default is OpenAI-compatible because the repository already has an OpenAI-compatible provider configuration shape. The PRD also defines Google, Qwen, DeepSeek, and Anthropic alternatives so teammates can choose based on availability, cost, and API access.

Every real-provider run should estimate cost before execution, record actual usage in `CostSummary`, and remain reproducible through pinned provider profiles and model versions.

## User Stories

1. As a project presenter, I want the demo to run without any API key, so that the final presentation is not blocked by network, billing, or quota failures.
2. As a project presenter, I want to enable real image generation only for final showcase runs, so that the project looks credible without wasting budget during development.
3. As a developer, I want planner, critic, and image generation to be separate model roles, so that I can tune cost and quality independently.
4. As a developer, I want provider selection to happen through configuration, so that switching suppliers does not require changing the pipeline.
5. As a developer, I want model versions pinned in provider profiles, so that demo outputs and cost estimates are reproducible.
6. As a developer, I want mock providers to remain the test default, so that automated tests do not call paid APIs.
7. As a teammate with an OpenAI key, I want an OpenAI provider profile, so that I can generate final demo images with the least integration friction.
8. As a teammate with Google API access, I want a Gemini and Imagen provider profile, so that I can use a lower-cost alternative for image generation.
9. As a teammate using domestic API access, I want Qwen text, vision, and image options, so that the project can still run when international APIs are inconvenient.
10. As a cost-conscious teammate, I want DeepSeek listed as a text-only planner option, so that cheap structured planning can be separated from expensive image generation.
11. As a reviewer, I want the PRD to explain why different roles use different models, so that the design looks intentional rather than arbitrary.
12. As a reviewer, I want to see cost estimates for all three demo scenarios, so that the real-provider plan is credible.
13. As a reviewer, I want mock and real-provider modes to produce the same report structure, so that the framework contribution is independent of provider choice.
14. As a project maintainer, I want API keys loaded only from environment variables, so that secrets are never committed to the repository.
15. As a project maintainer, I want provider errors written into reports, so that failed runs are diagnosable.
16. As a project maintainer, I want a pre-run estimate of image count and expected cost, so that a teammate can cancel an expensive run before spending money.
17. As a project maintainer, I want actual token counts, image counts, retry counts, and estimated spend recorded after a run, so that the team can compare budget predictions with reality.
18. As a researcher, I want to compare mock, low-cost, and final-quality provider profiles, so that the report can discuss trade-offs between reproducibility, cost, and output quality.
19. As a researcher, I want the critic model to run only on selected outputs, so that the project studies auditable review without making every run expensive.
20. As a scenario author, I want image quality settings to be declared per provider profile, so that story comics, game assets, and concept boards can share the same framework while using different quality budgets.
21. As a scenario author, I want retry budgets to remain scenario configuration, so that API cost scales with task difficulty and not hidden provider behavior.
22. As a developer, I want a cost estimator that handles retry buffers, so that a run with revision rounds does not surprise the team.
23. As a developer, I want real-provider smoke tests to be opt-in, so that CI and local tests remain free.
24. As a developer, I want failed provider calls to degrade into structured errors, so that partial reports can still be inspected.
25. As a teammate preparing slides, I want a simple table of recommended suppliers, models, and cost, so that the API decision can be explained quickly.
26. As a teammate preparing the final gallery, I want to spend most of the budget on image generation instead of planner tokens, so that visible output quality improves.
27. As a teammate preparing the final gallery, I want draft images generated with a cheap profile and final images generated with a higher-quality profile, so that iteration remains affordable.
28. As a teacher or evaluator, I want to see that ChatGPT subscriptions and API billing are separate, so that the team does not confuse product access with API budget.
29. As a future contributor, I want provider profiles to document pricing source dates, so that stale estimates can be refreshed.
30. As a future contributor, I want supplier-specific caveats documented, so that limitations such as transparent background support do not surprise downstream users.

## Implementation Decisions

- Keep mock as the default provider for development, tests, and no-key demos.
- Treat real APIs as optional provider profiles. A provider profile pins supplier, model version, role mapping, quality settings, and cost assumptions.
- Use three primary model roles: planner, critic, and image generator. Do not make every role use the same model.
- Recommended OpenAI profile:
  - Planner: `gpt-5.4-mini`
  - Critic: `gpt-5.4`, with `gpt-5.5` as a higher-quality option
  - Image generator: `gpt-image-2`, with `gpt-image-1-mini` as a low-cost draft option
- Recommended Google profile:
  - Planner and critic: `gemini-2.5-flash`
  - Image generator: Imagen 4 Fast for draft and Imagen 4 Standard for final runs
- Recommended Qwen profile:
  - Planner: `qwen-plus-2025-12-01`
  - Critic: `qwen-vl-plus-2025-08-15`
  - Image generator: `qwen-image-plus`
- Recommended DeepSeek usage:
  - Use `deepseek-v4-flash` only for text planning or prompt rewriting.
  - Do not use deprecated `deepseek-chat` or `deepseek-reasoner` as long-term model IDs.
- Recommended Anthropic usage:
  - Use Claude Haiku or Sonnet as optional text/vision critic alternatives.
  - Do not use Anthropic as the only provider profile because it does not cover image generation.
- Store API keys in environment variables only. The repository must not contain real keys, shared keys, or copied local credential files.
- Keep provider configuration compatible with the existing scenario `models` shape: each role resolves to a provider, model version, and optional parameters.
- Extend cost accounting around the existing `CostSummary` concept rather than introducing a separate budget object.
- Estimate costs before a real-provider run using planned asset count, retry budget, selected image quality, and role-level token assumptions.
- Record actual cost evidence after a run, including generation calls, retry calls, image generations, token counts when available, vision calls, and estimated spend.
- Use the following baseline estimate for the current three demos:
  - Story Comic: 5 generated images
  - Game Assets: 10 generated images
  - Concept Art Board: 8 generated images
  - Total: 23 generated images before retries
  - Text and vision planning estimate: about 21K input tokens and 9K output tokens across all three demos
- Recommended team budget:
  - $5 to $10 per teammate is enough for normal final-demo preparation.
  - $20 total team budget is comfortable if mock remains the default and real APIs are used only for final runs.
- Expected all-demo cost before retries:
  - OpenAI `gpt-5.4-mini` plus `gpt-image-2 medium`: about $1.28
  - OpenAI `gpt-5.4-mini` plus `gpt-image-2 high`: about $4.91
  - OpenAI `gpt-5.4-mini` plus `gpt-image-1-mini medium`: about $0.31
  - Google `gemini-2.5-flash` plus Imagen 4 Fast: about $0.49
  - Google `gemini-2.5-flash` plus Imagen 4 Standard: about $0.95
  - Qwen `qwen-plus` plus `qwen-image-plus`: about $0.70
- Add a 30 percent retry buffer for normal demo planning. If running all scenarios through multiple full revision rounds, image cost scales almost linearly with regenerated images.
- Do not rely on generated-image text for comic dialogue or UI labels. Continue using post-processing for text rendering and layout, because image models can still struggle with reliable text and precise composition.
- Document provider limitations in the provider profile. For example, if a selected image model does not support transparent backgrounds, game asset export should either use post-processing or another model.

## Testing Decisions

- Tests should verify external behavior: loaded configuration, selected provider role, estimated cost, recorded cost summary, generated report shape, and failure handling.
- Tests should not assert provider implementation internals or call real paid APIs by default.
- Keep existing end-to-end pipeline tests on mock providers.
- Add cost-estimator tests for each supported provider profile using deterministic input counts.
- Add tests for retry-buffer estimation, including zero-retry and max-revision scenarios.
- Add tests for missing API keys. The expected behavior is a structured provider error, not a crash with an unhelpful traceback.
- Add tests for provider profile validation, including unknown provider, unknown role, unsupported image quality, and missing model version.
- Add tests that real-provider mode writes the same report files as mock mode.
- Add tests that `CostSummary` records image generation counts and retry counts consistently with generated assets.
- Add opt-in smoke tests for real APIs guarded by environment variables. These should be skipped unless the relevant API key is present.
- Add documentation checks or snapshot tests for the provider recommendation table if it becomes part of generated reports.
- Similar prior art already exists in the repository around config loading, schema validation, evaluator behavior, revision decisions, and end-to-end pipeline tests.

## Out of Scope

- Purchasing API credits or managing teammate billing accounts.
- Building a centralized key-sharing system.
- Guaranteeing that provider pricing remains current after the PRD source date.
- Making real APIs mandatory for tests, CI, or the final presentation.
- Implementing every listed provider immediately.
- Benchmarking all providers for visual quality in a statistically rigorous way.
- Training or fine-tuning any image, text, or vision model.
- Replacing post-processed comic dialogue and UI labels with generated text inside images.
- Adding a complex YAML DSL for provider routing or budget logic.
- Choosing a single mandatory supplier for every teammate.

## Further Notes

- Pricing and model names in this PRD are based on official provider documentation checked on 2026-06-03.
- Cost estimates are API-only estimates. They exclude storage, local compute, network transfer, and any provider-specific taxes or account fees.
- API pricing changes frequently. The final report should include the date when pricing was checked and link to the official source pages.
- ChatGPT subscription access is separate from OpenAI API billing. A teammate with ChatGPT Plus or Team may still need a separately funded API account.
- Official pricing and model reference pages used for this PRD:
  - OpenAI pricing: https://developers.openai.com/api/docs/pricing
  - OpenAI latest model guidance: https://developers.openai.com/api/docs/guides/latest-model
  - OpenAI image generation guide: https://developers.openai.com/api/docs/guides/image-generation
  - Google Gemini pricing: https://ai.google.dev/gemini-api/docs/pricing
  - Anthropic Claude pricing: https://platform.claude.com/docs/en/about-claude/pricing
  - DeepSeek pricing: https://api-docs.deepseek.com/quick_start/pricing
  - Alibaba Cloud Model Studio pricing: https://www.alibabacloud.com/help/en/model-studio/models
