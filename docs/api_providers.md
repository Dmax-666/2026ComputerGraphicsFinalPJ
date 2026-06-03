# API Provider Profiles

Graphic Agent uses provider profiles to keep model selection separate from scenario logic. A scenario still declares visual workflow behavior, while a provider profile declares which supplier and model version should satisfy each model role.

## Default Behavior

The default profile is `mock`. It is the stable path for tests, offline demos, and presentation fallbacks. Mock runs do not require API keys and should keep producing the same report structure as real-provider runs.

`configs/default.yaml` names the default profile:

```yaml
providers:
  default: mock
```

Code can resolve a profile by name:

```python
from graphic_agent.config import resolve_provider_profile

profile = resolve_provider_profile("openai_compatible", "configs/providers")
```

CLI runs default to mock. A real-provider run must opt in explicitly:

```bash
graphic-agent run \
  --scenario configs/scenarios/story_comic.yaml \
  --input examples/story_comic_robot_cat.yaml \
  --output outputs/story_comic_real \
  --provider-profile configs/providers/openai_compatible.yaml
```

Estimate API spend before running a real provider:

```bash
graphic-agent estimate \
  --scenario configs/scenarios/story_comic.yaml \
  --input examples/story_comic_robot_cat.yaml \
  --provider-profile configs/providers/openai_compatible.yaml
```

Omitting `--provider-profile` estimates the default mock profile and should report zero API spend.

## Built-in Profiles

- `mock`: deterministic offline test and no-key demo provider.
- `openai_compatible`: recommended primary real-provider profile.
- `google`: Gemini plus Imagen fallback profile.
- `dashscope`: Qwen text, vision, and image profile.
- `deepseek`: text-only planner and prompt rewrite profile.
- `anthropic`: text and vision profile; requires another provider for image generation.

Each profile defines model roles under `models`. The common roles are `planner`, `critic`, and `image`; text-only profiles may omit image generation.

## Secrets

Profiles declare environment variable names only. Do not put real API keys in scenario YAML, provider YAML, reports, fixtures, or committed files.

Example:

```yaml
env:
  api_key: OPENAI_API_KEY
  base_url: OPENAI_BASE_URL
```

Use `validate_provider_environment` before a real-provider run. It reports which environment variables are required or missing, but never returns their values.

```python
from graphic_agent.config import load_provider_profile
from graphic_agent.provider_runtime import validate_provider_environment

profile = load_provider_profile("configs/providers/openai_compatible.yaml")
status = validate_provider_environment(profile)
```

From the CLI:

```bash
graphic-agent provider-check \
  --provider-profile configs/providers/openai_compatible.yaml
```

The command exits with code `1` when required environment variables are missing.

## Pricing Metadata

Provider profiles include pricing source metadata so demo cost estimates can be refreshed before the final presentation.

```yaml
pricing:
  source_checked_at: "2026-06-03"
  source_url: "https://developers.openai.com/api/docs/pricing"
```

## Pre-run Budget Estimates

Use `estimate_run_budget` before a real-provider run to show expected API spend without calling external services.

```python
from graphic_agent.config import load_provider_profile, load_scenario
from graphic_agent.costing import estimate_run_budget

scenario = load_scenario("configs/scenarios/story_comic.yaml")
profile = load_provider_profile("configs/providers/openai_compatible.yaml")
estimate = estimate_run_budget(scenario, profile, planned_asset_count=5)
```

The estimate reports planner, critic, image generation, and retry-buffer components. Mock estimates remain zero-cost.

## Actual Usage Reports

Real providers should attach usage metadata to generated assets or role-call results using the `ProviderUsage` shape. The pipeline merges this into `CostSummary`, so reports stay provider-neutral.

For image generation, `GeneratedAsset.metadata.provider_usage` may include:

```yaml
role: image
provider_profile: openai_compatible
provider: openai_compatible
model: gpt-image-2
image_generations: 1
estimated_cost_usd: 0.053
```

If usage metadata is absent, Graphic Agent falls back to deterministic mock-style image counts.

Provider exceptions should be converted with `capture_provider_failure` and recorded in `CostSummary.provider_failures`. Failure records include provider profile, role, model, reason, and retryability, but no credential values.
