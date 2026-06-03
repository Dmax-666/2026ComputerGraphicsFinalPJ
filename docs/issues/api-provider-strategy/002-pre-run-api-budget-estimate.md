# Issue 2: Pre-run API Budget Estimate

Type: AFK

## Parent

`docs/prd-api-provider-strategy.md`

## What to build

Add a pre-run cost estimate for real-provider runs. The estimate should use the selected provider profile, planned asset count, selected image quality, scenario retry budget, and model-role token assumptions to show expected spend before any paid API call happens.

The completed slice should make API cost visible from the CLI or Python API before execution, while keeping mock runs free and noise-free.

## Acceptance criteria

- [x] Cost estimation works without making external API calls.
- [x] Estimate includes planner, critic, image generation, and retry-buffer components.
- [x] Estimate supports the three current scenarios: Story Comic, Game Assets, and Concept Art Board.
- [x] Estimate can show a no-retry baseline and a configured retry-buffer total.
- [x] Estimate uses provider profile pricing assumptions rather than hardcoded provider names in the pipeline.
- [x] Tests cover zero-retry, normal retry-buffer, and all-three-demo estimates.

## Blocked by

Issue 1: Provider Profile Resolution.
