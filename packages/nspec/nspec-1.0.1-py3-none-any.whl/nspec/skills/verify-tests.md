---
description: Verify FR test cases (TC-XXX) have corresponding tests in the test suite
argument-hint: [spec-id (optional)]
---

Verify that all test cases defined in the FR have corresponding tests implemented.

1. Determine spec ID:
   - If "$1" is provided, use that
   - Otherwise, read from `.novabuilt.dev/nspec/state.json`
2. Use `verify_testcases` MCP tool with that spec_id and strict: true
3. Report the results clearly:
   - List matched test cases with their test file locations
   - List any missing test cases that need implementation
4. If test cases are missing, suggest what tests need to be written

This helps ensure test coverage before marking a spec complete.
