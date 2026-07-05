# Phase 1 — dev

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need.

## Task
Implement **Phase A — Genericize the topic** from `plans/library_transformation_plan.md`:

1. Add a `topic` section to `config/base/app.yaml` (`name`, `description`,
   `min_relevance_score`), with `description` copied verbatim from the current MCP
   definition in the prompt so behavior is unchanged.
2. Add `TopicConfig` to `src/config/config_manager.py` and a `topic: TopicConfig` field
   on `AppConfig` (optionally a `get_topic_config()` helper).
3. Parameterize the prompt in `config/base/prompts.yaml`: replace the hardcoded MCP text
   with `{topic_name}` / `{topic_description}`, ask the model to output `is_relevant`
   (not `is_mcp_related`), and register the two new variables. Keep the template
   `str.format`-safe (no stray literal braces).
4. In `AnthropicEvaluator`, load the topic and pass `topic_name`/`topic_description` into
   the `.format(...)` call; parse `is_relevant` from the response (with old-key fallback).
5. Rename the relevance field `is_mcp_related` → `is_relevant` in `ArticleEvaluation`
   (`src/models/evaluation.py`) and `URLEntry` (`src/models/url_registry.py`), and update
   all writers/readers: `src/evaluation/anthropic_client.py`, `src/evaluation/processor.py`,
   `src/utils/url_registry.py`, `src/stages/evaluate.py`, `src/stages/report.py`, and the
   CLI print in `src/cli/stage_commands.py`.
6. Add backward-compat reads so previously stored data (old `is_mcp_related` key in
   frontmatter and old parquet column) is still read correctly — the plan's "one-line
   shim, no migration." Exact locations are in context.md.
7. Update the affected tests (`tests/test_models/test_evaluation.py`,
   `tests/test_utils/test_url_registry.py`).

context.md lists every file, line, and the exact edits.

## In-scope files
- `config/base/app.yaml`
- `config/base/prompts.yaml`
- `src/config/config_manager.py`
- `src/evaluation/anthropic_client.py`
- `src/evaluation/processor.py`
- `src/models/evaluation.py`
- `src/models/url_registry.py`
- `src/utils/url_registry.py`
- `src/stages/evaluate.py`
- `src/stages/report.py`
- `src/cli/stage_commands.py`
- `tests/test_models/test_evaluation.py`, `tests/test_utils/test_url_registry.py`

## Out of scope
- `src/templates/*.html` "MCP Monitor" strings (deferred).
- Wiring `topic.min_relevance_score` into the report filter plumbing.
- Collections, sources, packaging (later phases).

## Mode
Unconstrained delivery. Make it work and clean enough to commit. Don't worry about review
nits — that belongs to the review step. Follow the repo's MVP principles: minimal, no
extra abstractions. The only `is_mcp_related` references that may remain are the
documented backward-compat fallback reads.

## Contract
- Run `uv run poe check` (ruff + ty + pytest) and get it green before committing.
- Finish by running `git commit` so pre-commit hooks execute.
- If hooks fail, address findings and re-commit until clean.
- Multiple commits OK. Do NOT skip hooks (no `--no-verify`). Do NOT push.

## Report
Return ONLY this JSON:
{"commit_shas": ["..."], "summary": "one sentence", "deviations": ["..."], "unresolved_issues": ["..."]}
