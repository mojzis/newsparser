# Phase 1 — review

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need.

## Review skill
python-review

## Commit range
Use the base sha the orchestrator gives you for this phase..HEAD (the Phase 1 dev commits).

## Task
1. Invoke the review skill (use the `Skill` tool) over the commit range.
2. For each finding, decide if it's real and actionable. Drop false positives and
   pre-existing issues.
3. Report only. Do NOT fix anything, do NOT commit.

## Focus notes for this phase
- This is new config-model code + two YAMLs + tests. Watch for: the Pydantic
  `model_config` reserved-name gotcha (see context.md), over-engineering beyond MVP
  (needless abstractions/validators), and whether `mcp.yaml` truly reproduces the current
  `config/base/app.yaml` topic/ui (a drift here silently changes behavior later).
- Do NOT flag the deliberately-out-of-scope items: unwired `topic.min_relevance_score`,
  auxiliary-output namespacing, and the absence of CLI/stage wiring (that's Phase 2).

## Report
Return ONLY this JSON:
{"findings": [{"description": "...", "file": "...", "severity": "high|medium|low"}], "dropped": ["finding + why not actionable"], "deviations": ["..."]}
