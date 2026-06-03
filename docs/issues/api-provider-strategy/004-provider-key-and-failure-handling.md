# Issue 4: Provider Key and Failure Handling

Type: AFK

## Parent

`docs/prd-api-provider-strategy.md`

## What to build

Add safe handling for real-provider credentials and provider failures. Real-provider runs should read API keys only from environment variables declared by the selected profile, and failures should become structured report data instead of unhelpful crashes.

The completed slice should protect secrets, keep tests offline, and make failed API runs diagnosable.

## Acceptance criteria

- [ ] Real provider profiles declare required environment variable names for credentials.
- [ ] Missing API keys produce clear structured errors before paid calls are attempted.
- [ ] Provider call failures are captured in reports with provider, role, model, and failure reason.
- [ ] No real API keys are written to reports, logs, fixtures, or committed files.
- [ ] Real-provider tests are opt-in and skipped unless the relevant API key is present.
- [ ] Offline tests cover missing-key and provider-error behavior with fake providers.

## Blocked by

Issue 1: Provider Profile Resolution.

