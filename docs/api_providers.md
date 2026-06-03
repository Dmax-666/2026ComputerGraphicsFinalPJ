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

## Pricing Metadata

Provider profiles include pricing source metadata so demo cost estimates can be refreshed before the final presentation.

```yaml
pricing:
  source_checked_at: "2026-06-03"
  source_url: "https://developers.openai.com/api/docs/pricing"
```

