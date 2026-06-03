# Issue 1: Provider Profile Resolution

Type: AFK

## Parent

`docs/prd-api-provider-strategy.md`

## What to build

Add a provider profile layer that lets Graphic Agent resolve model roles from configuration without changing the pipeline. A profile should name the supplier, model versions, role mapping, quality settings, pricing assumptions, and environment variable names needed for the run.

The completed slice should allow the mock profile, OpenAI-compatible profile, Google profile, Qwen profile, DeepSeek text-only profile, and Anthropic text/vision profile to be represented consistently. The pipeline should still default to mock behavior when no real provider profile is selected.

## Acceptance criteria

- [ ] A provider profile can define planner, critic, and image generator model roles independently.
- [ ] Unknown providers, missing role mappings, and missing model versions fail with clear validation errors.
- [ ] Mock remains the default provider profile for tests and no-key demos.
- [ ] Provider profiles can pin pricing source dates and supplier-specific caveats.
- [ ] Configuration tests cover the mock profile and at least one real-provider profile.
- [ ] Documentation explains how a scenario selects a provider profile without embedding API keys.

## Blocked by

None - can start immediately.

