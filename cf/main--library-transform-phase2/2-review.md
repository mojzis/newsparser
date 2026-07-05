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
