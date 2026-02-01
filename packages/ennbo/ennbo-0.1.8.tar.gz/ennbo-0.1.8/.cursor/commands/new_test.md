# Systematic Test-Probing Command

BEFORE: Be sure all tests pass: pytest, ruff, & kiss
1. Introduce a minimal, isolated semantic change that alters algorithm behavior (not formatting).
2. Run the relevant tests to see whether the change is detected.
3. If tests do not fail, write the broadest, deterministic unit test that should fail with the bug.
4. Run the new test and confirm it fails with the bug in place.
5. Revert the semantic change and rerun the test to confirm it passes.
6. Keep the change set minimal and document the specific coverage gap the new test closes.
AFTER: Be sure all tests pass: pytest, ruff, & kiss

Finall, summarize for the user.
