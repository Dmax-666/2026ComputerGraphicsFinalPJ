# API Provider Strategy Issues

Parent PRD: `docs/prd-api-provider-strategy.md`

This issue set breaks the API provider strategy into tracer-bullet slices. Each slice should leave Graphic Agent in a demoable or testable state without making paid API calls by default.

## Current Status

1. **Provider profile resolution**
   - Type: AFK
   - Status: Done
   - Blocked by: None
   - User stories covered: 3, 4, 5, 7, 8, 9, 10, 14, 29, 30

2. **Pre-run API budget estimate**
   - Type: AFK
   - Status: Done
   - Blocked by: Issue 1
   - User stories covered: 12, 16, 17, 22, 25, 26, 27

3. **Actual provider usage in CostSummary**
   - Type: AFK
   - Status: Done
   - Blocked by: Issue 1
   - User stories covered: 13, 17, 18, 21, 24

4. **Provider key and failure handling**
   - Type: AFK
   - Status: Done
   - Blocked by: Issue 1
   - User stories covered: 1, 6, 14, 15, 23, 24, 28

5. **OpenAI-compatible real-provider tracer path**
   - Type: AFK
   - Status: Done
   - Blocked by: Issues 1, 3, 4
   - User stories covered: 2, 7, 13, 15, 19, 20, 23

6. **Final demo profile and pricing review**
   - Type: HITL
   - Status: Partially prepared; waiting on team decisions and API access
   - Blocked by: Issues 1, 2, 5
   - User stories covered: 2, 11, 12, 25, 26, 27, 29, 30
