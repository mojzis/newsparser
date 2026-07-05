# Phase 1 — fix

See [context.md](./context.md) — required reading.

## Task
Fix the review findings below. Fix only these — no drive-by changes.

## Findings
[{"description": "test_mcp_matches_base_app_config docstring promises the mcp collection 'must reproduce today's base app config exactly' (the core invariant of this phase), but only asserts three topic.* fields. The parts that can actually drift and silently change behavior later -- ui (site_title/tagline/theme), evaluation (prompt_config/model_config_name vs base default_prompt_config/default_model_config), and the searches key set -- are untested. Extend assertions to cover ui, evaluation, and searches keys against config/base/app.yaml and config/base/searches.yaml.", "file": "/home/matous/git/newsparser/tests/test_config/test_collection.py", "severity": "medium"}]

## Contract
- Finish by running `git commit` so pre-commit hooks execute. No `--no-verify`. Do NOT push.
- If a finding is wrong or unfixable, skip it and say why in `deviations`.

## Report
Return ONLY this JSON:
{"commit_shas": ["..."], "summary": "one sentence", "deviations": ["..."], "unresolved_issues": ["..."]}
