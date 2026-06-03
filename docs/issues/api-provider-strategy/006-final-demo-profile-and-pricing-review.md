# Issue 6: Final Demo Profile and Pricing Review

Type: HITL

## Parent

`docs/prd-api-provider-strategy.md`

## What to build

Prepare the human-reviewed final API demo plan. Refresh provider pricing, choose the final demo profile, confirm which teammate owns the API key, and decide which images should be regenerated with real models for the final gallery.

This slice is HITL because it involves current pricing, billing access, API key ownership, and final quality judgment.

## Acceptance criteria

- [ ] Pricing is refreshed against official provider pages and the checked date is recorded.
- [ ] The team chooses one primary final-demo provider profile and one fallback profile.
- [ ] The team confirms who owns API key setup and that keys will remain outside the repository.
- [ ] The team selects which scenario outputs should be generated with real image models.
- [ ] The final demo budget includes baseline cost and retry-buffer cost.
- [ ] The final report explains why mock remains the reproducible baseline even when real images are shown.

## Blocked by

- Issue 1: Provider Profile Resolution.
- Issue 2: Pre-run API Budget Estimate.
- Issue 5: OpenAI-compatible Real-provider Tracer Path.

