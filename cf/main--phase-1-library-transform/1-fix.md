# Phase 1 — fix

See [context.md](./context.md) — required reading.

## Task
Fix the review findings below. Fix only these — no drive-by changes.

## Findings
[{"description": "Prompt genericization is incomplete: in config/base/prompts.yaml the relevance_score instruction line still hardcodes the topic — `2. relevance_score (0.0-1.0): How relevant is this to {topic_name}? 0=unrelated, 1=directly about MCP`. Every other topic reference on that line was templated to {topic_name}, but `1=directly about MCP` was left. context.md line 46 explicitly required the relevance_score wording that mentions MCP to become {topic_name}. This is an accidental leftover (not the intentionally-kept key_topics BAD-examples list). It doesn't break str.format (it's plain text, not a stray brace), but it defeats the genericization goal for any non-MCP topic. Fix: `1=directly about {topic_name}`.", "file": "config/base/prompts.yaml", "severity": "medium"}, {"description": "Newly-added comment in src/evaluation/anthropic_client.py (~line 178) justifies the is_mcp_related fallback as guarding against a 'stale (cached) template that still asked for is_mcp_related'. Prompt caching does not change the model's output field names, so the stated rationale is inaccurate; the real reason for the fallback is a model still emitting the old key or an in-flight deploy. The fallback code itself is correct and intended — only the comment's explanation is misleading. Minor.", "file": "src/evaluation/anthropic_client.py", "severity": "low"}]

## Contract
- Finish by running `git commit` so pre-commit hooks execute. No `--no-verify`. Do NOT push.
- If a finding is wrong or unfixable, skip it and say why in `deviations`.

## Report
Return ONLY this JSON:
{"commit_shas": ["..."], "summary": "one sentence", "deviations": ["..."], "unresolved_issues": ["..."]}
