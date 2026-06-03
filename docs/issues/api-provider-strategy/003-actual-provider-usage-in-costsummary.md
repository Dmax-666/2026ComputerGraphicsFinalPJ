# Issue 3: Actual Provider Usage in CostSummary

Type: AFK

## Parent

`docs/prd-api-provider-strategy.md`

## What to build

Extend run accounting so actual provider usage is recorded in `CostSummary` and written to the normal report outputs. The report should remain provider-neutral: mock runs count generated images and retry calls, while real-provider runs can also include token counts, vision calls, image quality, and estimated spend.

The completed slice should make real and mock runs comparable through the same report shape.

## Acceptance criteria

- [ ] `CostSummary` records generated images, retry calls, per-asset attempts, vision calls, token counts when available, and estimated spend.
- [ ] Mock runs continue to populate cost fields deterministically without paid API data.
- [ ] Real-provider usage metadata can be merged into `CostSummary` without changing scenario code.
- [ ] `reports/cost_summary.json` and `reports/result.json` include the updated accounting.
- [ ] Tests verify cost fields stay consistent with generated assets and retry rounds.
- [ ] Tests verify missing provider usage metadata does not break mock runs.

## Blocked by

Issue 1: Provider Profile Resolution.

