# Phase 2 — review

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need.

## Review skill
python-review

## Commit range
Use the base sha the orchestrator gives you for this phase..HEAD (the Phase 2 dev commits).

## Task
1. Invoke the review skill (use the `Skill` tool) over the commit range.
2. For each finding, decide if it's real and actionable. Drop false positives and
   pre-existing issues.
3. Report only. Do NOT fix anything, do NOT commit.

## Focus notes for this phase
- Correctness of path routing: every cross-stage read in report.py (fetch/collect dirs) and
  every write must land under the collection namespace — a missed literal silently reads the
  wrong collection's data. Verify none remain.
- The evaluator's default fallback (no collection passed) must still behave exactly as
  before for existing callers/tests.
- CLI plumbing duplication across ~8 commands is expected; flag only genuinely error-prone
  duplication, not MVP-acceptable repetition.
- Do NOT flag: templates still saying "MCP Monitor" (that is Phase 3), auxiliary-output not
  being namespaced (out of scope), or unwired `topic.min_relevance_score`.

## Report
Return ONLY this JSON:
{"findings": [{"description": "...", "file": "...", "severity": "high|medium|low"}], "dropped": ["finding + why not actionable"], "deviations": ["..."]}

## Deviations from earlier steps
- phase 1 dev: EvaluationSelection uses a Field alias (model_config_name -> YAML key model_config) with populate_by_name=True, per context.md's suggested approach.
- phase 1 dev: Committed the untracked cf/ orchestration files alongside the code changes since the brief specifies `git add -A`.
- phase 2 dev: Dropped the --config/config_path search-config override from collect and run_all in both stage_commands.py and new_commands.py (searches are now sourced solely from the loaded collection); legacy onsp commands in src/cli/legacy_commands.py still keep --config unchanged since they're out of scope.
- phase 2 dev: Added a small load_collection_or_exit helper in stage_commands.py so status/list_files/clean surface an unknown --collection as a clean CLI error (exit 1) instead of an unhandled FileNotFoundError traceback; collect/fetch/evaluate/report already had a wrapping try/except so load_collection is called directly there.
- phase 2 dev: Added new test files (tests/test_evaluation/test_anthropic_client.py, tests/test_stages/test_report_stage.py, tests/test_cli/test_stage_commands.py) beyond the explicitly named in-scope files, per the brief's allowance to extend tests as needed for collection-aware paths/evaluator.

## Deviations from earlier steps
- phase 1 dev: EvaluationSelection uses a Field alias (model_config_name -> YAML key model_config) with populate_by_name=True, per context.md's suggested approach.
- phase 1 dev: Committed the untracked cf/ orchestration files alongside the code changes since the brief specifies `git add -A`.
