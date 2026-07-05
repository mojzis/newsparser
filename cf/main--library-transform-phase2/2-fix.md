# Phase 2 — fix

See [context.md](./context.md) — required reading.

## Task
Fix the review findings below. Fix only these — no drive-by changes.

## Findings
[{"description": "Inconsistent unknown-collection error handling. The new load_collection_or_exit helper (stage_commands.py:37) gives a clean '❌ <FileNotFoundError msg>' + exit 1 and is used by status/list_files/clean, but collect (line 121), fetch (line 208), evaluate (line 263) and report (line 364) call bare load_collection() inside their broad except Exception, so a bad --collection is mislabeled as a stage failure instead of a config error. Calling load_collection_or_exit before each command's try block would make the message correct and consistent.", "file": "src/cli/stage_commands.py", "severity": "low"}, {"description": "Fragile test coupling in test_missing_search_option_uses_collection_default (test_stage_commands.py:60): it asserts the \"using search 'duckdb_mentions'\" console line prints, relying on collect() reaching that print before failing on missing credentials. If the credential check ever moves ahead of search resolution the test breaks without a real regression. Prefer asserting on the resolved search via a more direct seam, or document the ordering dependency.", "file": "tests/test_cli/test_stage_commands.py", "severity": "low"}]

## Contract
- Finish by running `git commit` so pre-commit hooks execute. No `--no-verify`. Do NOT push.
- If a finding is wrong or unfixable, skip it and say why in `deviations`.

## Report
Return ONLY this JSON:
{"commit_shas": ["..."], "summary": "one sentence", "deviations": ["..."], "unresolved_issues": ["..."]}
