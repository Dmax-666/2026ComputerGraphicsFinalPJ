# Issue 5: OpenAI-compatible Real-provider Tracer Path

Type: AFK

## Parent

`docs/prd-api-provider-strategy.md`

## What to build

Implement a narrow OpenAI-compatible provider path that proves the framework can swap mock components for real planner, critic, and image generation roles without changing scenario logic. This should be a tracer bullet, not a full provider marketplace.

The completed slice should support an optional real-provider run for at least one existing scenario, while keeping the same structured intermediate reports as mock mode.

## Acceptance criteria

- [x] Planner, critic, and image generator roles can resolve to OpenAI-compatible model settings.
- [x] The real-provider path returns structured pipeline objects rather than passing free-form text between stages.
- [x] At least one existing scenario can run through the OpenAI-compatible path when a valid key is present.
- [x] The same report files are produced in mock mode and OpenAI-compatible mode.
- [x] Tests use fake transports or skipped opt-in smoke tests, not mandatory paid calls.
- [x] Documentation states that real-provider mode is optional and mock remains the stable demo path.

## Blocked by

- Issue 1: Provider Profile Resolution.
- Issue 3: Actual Provider Usage in CostSummary.
- Issue 4: Provider Key and Failure Handling.
