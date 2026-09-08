# Phase 2 — fix

See [context.md](./context.md) — required reading.

## Task
Fix the review findings below. Fix only these — no drive-by changes.

## Findings
- Test name/behavior mismatch: `test_hackernews_only_skips_bluesky_client` in tests/test_stages/test_collect_stage.py asserts only that `stage.sources` has no 'bluesky' key. But `CollectStage.__init__` (src/stages/collect.py:62) unconditionally constructs `self.bluesky_client = BlueskyClient(settings)` even for hackernews-only collections — the Bluesky *source* is skipped, the *client object* is not. The name implies the client isn't built. Rename to `test_hackernews_only_skips_bluesky_source` (the docstring already correctly says 'no Bluesky source is built') so it doesn't mislead a reader into thinking the client is conditionally constructed. (file: tests/test_stages/test_collect_stage.py, severity: low)

## Contract
- Finish by running `git commit` so pre-commit hooks execute. No `--no-verify`. Do NOT push.
- If a finding is wrong or unfixable, skip it and say why in `deviations`.

## Report
Return ONLY this JSON:
{"commit_shas": ["..."], "summary": "one sentence", "deviations": ["..."], "unresolved_issues": ["..."]}
