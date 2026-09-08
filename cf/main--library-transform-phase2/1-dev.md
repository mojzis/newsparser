# Phase 1 — dev

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need.

## Task
Build the Collection config data layer. No pipeline wiring in this phase.

1. Create `src/config/collection.py` with:
   - `EvaluationSelection` submodel (`prompt_config`, and a model-selection field — mind the
     Pydantic `model_config` reserved-name gotcha noted in context.md; pick a safe field
     name / YAML key and keep it consistent for later phases).
   - `CollectionConfig` reusing `TopicConfig` and `UIConfig` from
     `src.config.config_manager` and `SearchConfig` from `src.config.searches`. Fields:
     `name`, `topic`, `ui`, `evaluation`, `searches`, `default_search`. Add
     `stages_base` → `Path("stages")/name` and `output_base` → `Path("output")/name`
     properties. Add a validator (or check in the loader) that `default_search` names an
     enabled search in `searches`.
   - `load_collection(name, config_dir="config") -> CollectionConfig` reading
     `config_dir/collections/<name>.yaml`; raise a clear error for an unknown name.
2. Create `config/collections/mcp.yaml` reproducing today's config exactly (topic + ui
   copied from `config/base/app.yaml`; evaluation → `mcp_evaluation_v1` / `mcp_evaluator_v1`;
   searches = full inline copy of `config/base/searches.yaml`; `default_search: mcp_tag`).
3. Create `config/collections/duckdb.yaml` — a second, genuinely different topic (see
   context.md for the agreed shape: DuckDB topic/ui, reuse the generic prompt+model, one or
   two duckdb searches, `default_search: duckdb_mentions`).
4. Add `tests/test_config/test_collection.py`: load both collections; assert the `mcp`
   collection's topic name/description/min_relevance_score match `config/base/app.yaml`;
   assert `stages_base == Path("stages/mcp")` and `output_base == Path("output/mcp")`;
   assert `duckdb` resolves its own topic/ui and `default_search`; assert an unknown
   collection name raises; assert `searches.get_search(default_search)` is enabled.

## In-scope files
- `src/config/collection.py` (new)
- `config/collections/mcp.yaml` (new)
- `config/collections/duckdb.yaml` (new)
- `tests/test_config/test_collection.py` (new)

## Out of scope
- Any change to CLI, stages, evaluator, templates, or existing config files.
- Wiring `topic.min_relevance_score` anywhere.
- Namespacing auxiliary output (stats/about/publish/present).

## Mode
Unconstrained delivery. Make it work and clean enough to commit. Don't worry about review nits — that belongs to the review step.

## Contract
- Run `uv run poe check` (ruff + ty + pytest) and make it green before committing — there
  are no pre-commit hooks, so nothing else enforces this.
- Sanity-check the YAMLs actually load, e.g.
  `uv run python -c "from src.config.collection import load_collection; load_collection('mcp'); load_collection('duckdb')"`.
- Finish by running `git commit` (use `git add -A`; footer `🤖 Generated with [Claude Code](https://claude.ai/code)`).
- If hooks/checks fail, address findings and re-commit until clean.
- Multiple commits OK. Do NOT skip hooks (no `--no-verify`). Do NOT push.

## Report
Return ONLY this JSON:
{"commit_shas": ["..."], "summary": "one sentence", "deviations": ["..."], "unresolved_issues": ["..."]}
