# Phase 2 — check

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need.

## Verifies
The pipeline is collection-aware end to end: a `--collection` flag on all stage commands
(default `mcp`), stages instantiated with the collection's namespaced `base_path`, the
collector/report using the collection's searches/paths, the evaluator using the
collection's topic + prompt/model, and report.py's previously-hardcoded stage/output paths
now routed under the collection. Existing default (`mcp`) behavior is preserved.

## Verification steps
1. `uv run poe check` — ruff clean, ty clean, full pytest green. Paste the tail.
2. `--collection` present on `collect`, `fetch`, `evaluate`, `report`, `run_all`,
   `status`, `list_files`, `clean` (check `uv run nsp status --help`,
   `uv run nsp collect --help`, etc.) and defaults to `mcp`.
3. Path routing (no network): `uv run nsp status --collection duckdb` references
   `stages/duckdb/…`; `uv run nsp status --collection mcp` (or no flag) references
   `stages/mcp/…`. `list_files`/`clean` scan the collection's dir.
4. `grep -n 'stages/fetch\|stages/collect\|Path("output")' src/stages/report.py` — the
   previously-hardcoded literals should be gone (replaced by `self.base_path/…` and the
   collection output dir). Confirm `ReportStage` builds `ReportGenerator` with the
   collection's `output_base`.
5. Evaluator is collection-aware: `AnthropicEvaluator` resolves topic/prompt/model from a
   passed collection and still falls back to defaults with no collection. Confirm by
   constructing it with a dummy `Settings` and the `duckdb` collection (no API call) and
   checking `.topic.name` is the duckdb topic; and that `_create_evaluation_prompt` renders
   the duckdb topic name, no unfilled `{topic_` placeholder.
6. Collector sources searches from the collection: `--collection duckdb` with no `--search`
   uses `duckdb`'s `default_search`.
7. `git show --stat HEAD` (and any earlier phase-2 commits) touch only in-scope files.

## Pass condition
`poe check` green; `--collection` on all listed commands; duckdb vs mcp route to distinct
`stages/<name>` and `output/<name>` dirs; no hardcoded `stages/fetch|stages/collect|
Path("output")` left in report.py; evaluator resolves the collection's topic/prompt/model
with a working default fallback.

## Constraints
- Read-only. Do NOT modify code or commit. Do NOT call Bluesky/Anthropic. If broken, report it — do not fix it.

## Report
Return ONLY this JSON:
{"verified": true, "evidence": "what you observed (paste output)", "deviations": ["..."], "issues": ["..."]}

## Deviations from earlier steps
- phase 1 dev: EvaluationSelection uses a Field alias (model_config_name -> YAML key model_config) with populate_by_name=True, per context.md's suggested approach.
- phase 1 dev: Committed the untracked cf/ orchestration files alongside the code changes since the brief specifies `git add -A`.
- phase 2 dev: Dropped the --config/config_path search-config override from collect and run_all in both stage_commands.py and new_commands.py (searches are now sourced solely from the loaded collection); legacy onsp commands in src/cli/legacy_commands.py still keep --config unchanged since they're out of scope.
- phase 2 dev: Added a small load_collection_or_exit helper in stage_commands.py so status/list_files/clean surface an unknown --collection as a clean CLI error (exit 1) instead of an unhandled FileNotFoundError traceback; collect/fetch/evaluate/report already had a wrapping try/except so load_collection is called directly there.
- phase 2 dev: Added new test files (tests/test_evaluation/test_anthropic_client.py, tests/test_stages/test_report_stage.py, tests/test_cli/test_stage_commands.py) beyond the explicitly named in-scope files, per the brief's allowance to extend tests as needed for collection-aware paths/evaluator.

## Additional verification (post-review fixes)
Verify each of these findings was addressed:
- collect/fetch/evaluate/report now call load_collection_or_exit (or equivalent) before their try blocks so an unknown --collection produces a clean config error instead of being mislabeled as a stage failure.
- test_missing_search_option_uses_collection_default no longer relies on fragile ordering between the credential check and the search-resolution print (or the ordering dependency is documented).

## Deviations from earlier steps
- phase 1 dev: EvaluationSelection uses a Field alias (model_config_name -> YAML key model_config) with populate_by_name=True, per context.md's suggested approach.
- phase 1 dev: Committed the untracked cf/ orchestration files alongside the code changes since the brief specifies `git add -A`.
