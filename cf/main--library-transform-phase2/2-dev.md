# Phase 2 — dev

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need. Phase 1 delivered `src/config/collection.py`, `config/collections/{mcp,duckdb}.yaml`, and tests — build on them.

## Task
Thread the collection through the CLI and stages so the whole pipeline runs per collection
with namespaced paths. Default collection = `mcp`, so existing invocations keep working.

1. Add `--collection` option (default `"mcp"`) to these commands in
   `src/cli/stage_commands.py`: `collect`, `fetch`, `evaluate`, `report`, `run_all`,
   `status`, `list_files`, `clean`. In each, `collection = load_collection(name)`.
   Mirror the option on the matching convenience wrappers in `src/cli/new_commands.py`
   and pass it through their `ctx.invoke(...)` calls.
2. Pass `base_path=collection.stages_base` to `CollectStage`, `FetchStage`,
   `EvaluateStage`, `ReportStage`. `status`/`list_files`/`clean` must scan
   `collection.stages_base` instead of hardcoded `Path("stages")`.
3. `collect`: use the collection's searches — `collection.searches.get_search(search)` and
   default `--search` to the collection's `default_search` when not provided (so
   `--collection duckdb` doesn't need `--search`). Keep the `--config` path override
   behavior only if trivial; otherwise it's fine to source searches solely from the
   collection (note this as a deviation if you drop `--config`).
4. Make `EvaluateStage` accept the collection and pass it to `AnthropicEvaluator`; update
   `AnthropicEvaluator.__init__` to resolve topic + prompt + model from the collection when
   given (topic = `collection.topic`, prompt = `get_prompt_config(collection.evaluation.
   <prompt field>)`, model = `get_model_config(collection.evaluation.<model field>)`),
   falling back to today's global defaults when no collection is passed.
5. Fix the hardcoded paths inside `src/stages/report.py` so they are collection-aware:
   `Path("stages/fetch")`, the `"stages/collect"` string, `Path("stages/collect")`, and
   the report output `Path("output")/"reports"/…`. Use `self.base_path/…` for cross-stage
   reads and build `ReportGenerator(output_dir=collection.output_base)` for writes. Give
   `ReportStage` whatever param it needs (`output_base` or the whole collection) to do this.
6. Leave auxiliary commands (`render_stats`, `render_about`, `publish`, `present`) writing
   to `output/` root — out of scope for per-collection namespacing this run.
7. Do NOT change site branding/templates yet (that's Phase 3) — text may still read
   "MCP Monitor"; only data/paths/config routing changes here.

## In-scope files
- `src/cli/stage_commands.py`
- `src/cli/new_commands.py`
- `src/stages/evaluate.py`
- `src/stages/report.py`
- `src/evaluation/anthropic_client.py`
- Tests as needed under `tests/` (e.g. extend for collection-aware paths / evaluator)

## Out of scope
- Templates and `ReportGenerator` render context (Phase 3).
- Namespacing auxiliary output.
- Wiring `topic.min_relevance_score`.

## Mode
Unconstrained delivery. Make it work and clean enough to commit. Don't worry about review nits — that belongs to the review step.

## Contract
- Run `uv run poe check` (ruff + ty + pytest) green before committing — no pre-commit
  hooks exist, so you must run it yourself.
- Verify routing without external APIs: e.g. `uv run nsp status --collection duckdb`
  should reference `stages/duckdb/…`, and `uv run nsp status --collection mcp` should
  reference `stages/mcp/…`. Do NOT call Bluesky/Anthropic (no creds; not needed to prove
  path/config routing).
- Finish by running `git commit` (`git add -A`; footer `🤖 Generated with [Claude Code](https://claude.ai/code)`).
- If checks fail, fix and re-commit until clean. Multiple commits OK. No `--no-verify`. Do NOT push.

## Report
Return ONLY this JSON:
{"commit_shas": ["..."], "summary": "one sentence", "deviations": ["..."], "unresolved_issues": ["..."]}

## Deviations from earlier steps
- phase 1 dev: EvaluationSelection uses a Field alias (model_config_name -> YAML key model_config) with populate_by_name=True, per context.md's suggested approach.
- phase 1 dev: Committed the untracked cf/ orchestration files alongside the code changes since the brief specifies `git add -A`.
