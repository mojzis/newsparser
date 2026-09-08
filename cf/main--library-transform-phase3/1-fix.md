# Phase 1 — fix

See [context.md](./context.md) — required reading.

## Task
Fix the review findings below. Fix only these — no drive-by changes.

## Findings
- Misleading test: `test_search_returns_bluesky_stamped_posts` in tests/test_sources/test_bluesky.py (docstring 'stamped as bluesky', assertion `all(post.source == 'bluesky' for post in result)`) verifies no behavior. `BlueskySource.search` does not stamp source — its own docstring says so — so the assertion is trivially true because the `sample_posts` fixture already carries the model default 'bluesky'. This gives false confidence that source-stamping is tested. Rename to reflect delegation/context behavior or drop the source assertion (the meaningful behavior is already covered by the delegation and __aenter__/__aexit__ asserts). (file: tests/test_sources/test_bluesky.py, severity: low)

## Contract
- Finish by running `git commit` so pre-commit hooks execute. No `--no-verify`. Do NOT push.
- If a finding is wrong or unfixable, skip it and say why in `deviations`.

## Report
Return ONLY this JSON:
{"commit_shas": ["..."], "summary": "one sentence", "deviations": ["..."], "unresolved_issues": ["..."]}
