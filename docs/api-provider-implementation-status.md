# API Provider Strategy Implementation Status

Last verified: 2026-06-03

Parent PRD: `docs/prd-api-provider-strategy.md`

Issue set: `docs/issues/api-provider-strategy/`

## Current Status

The AFK implementation slices are complete and committed. The remaining work is HITL final-demo approval: API key ownership, primary/fallback provider approval, final real-model run selection, and gallery review.

## Completed Issues

| Issue | Status | Evidence |
|---|---|---|
| 1. Provider profile resolution | Done | `8294e5e feat: add auditable provider profile baseline` |
| 2. Pre-run API budget estimate | Done | `7e76ea8 feat: estimate provider run budgets`, `00eaf79 feat: expose budget estimates in cli` |
| 3. Actual provider usage in `CostSummary` | Done | `5110d18 feat: record provider usage in cost summaries` |
| 4. Provider key and failure handling | Done | `b6ff04e feat: add safe provider runtime checks`, `12be115 feat: add provider environment check cli` |
| 5. OpenAI-compatible real-provider tracer path | Done | `a24abf3 feat: add openai compatible provider tracer` |
| 6. Final demo profile and pricing review | HITL pending | `da2191a docs: prepare final api demo review`, `docs/final-demo-api-review.md` |

## Verification Commands

Run the full local validation suite:

```bash
python -m pytest -q
python -m ruff check .
```

Latest verified result:

- `67 passed`
- `ruff check .`: all checks passed

## Demo Commands

Estimate cost without API calls:

```bash
graphic-agent estimate \
  --scenario configs/scenarios/story_comic.yaml \
  --input examples/story_comic_robot_cat.yaml \
  --provider-profile configs/providers/openai_compatible.yaml
```

Check provider environment safely:

```bash
graphic-agent provider-check \
  --provider-profile configs/providers/openai_compatible.yaml
```

Run the stable mock demo:

```bash
graphic-agent run \
  --scenario configs/scenarios/story_comic.yaml \
  --input examples/story_comic_robot_cat.yaml \
  --output outputs/story_comic_robot_cat
```

Run the optional real-provider path after HITL approval:

```bash
graphic-agent run \
  --scenario configs/scenarios/story_comic.yaml \
  --input examples/story_comic_robot_cat.yaml \
  --output outputs/story_comic_real \
  --provider-profile configs/providers/openai_compatible.yaml
```

## Architecture Notes

- `ProviderProfile` and `ModelSpec` keep provider choice out of scenario logic.
- `provider_runtime.py` owns model-role lookup, environment checks, and structured provider failures.
- `costing.py` owns pre-run estimates and actual `CostSummary` accounting.
- `tools/openai_compatible.py` is an optional real-provider tracer with fake-transport tests.
- `pipeline.py` remains the orchestrator; it accepts injected image generators for tests and optional real-provider runs.

## Remaining HITL Decisions

- [ ] Confirm API key owner.
- [ ] Run `provider-check` on the demo machine.
- [ ] Approve primary profile.
- [ ] Approve fallback profile.
- [ ] Choose which scenario outputs should be generated with real models.
- [ ] Review generated gallery assets.
- [ ] Refresh pricing assumptions on the final report date.

