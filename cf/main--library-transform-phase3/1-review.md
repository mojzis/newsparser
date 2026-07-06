# Phase 1 — review

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need.

## Review skill
python-review

## Commit range
<base sha for this phase — provided by orchestrator; overall plan base is fd7c507>..HEAD

## Task
1. Invoke the review skill (use the `Skill` tool) over the commit range.
2. For each finding, decide if it's real and actionable. Drop false positives and pre-existing
   issues. Keep MVP scope in mind: the `Source` protocol is intentionally minimal (one impl this
   phase), expansion stays in `CollectStage` by design, and `BlueskyPost` keeps its name — none of
   those are defects to flag. Do flag genuine issues in the new `source` field, the protocol/adapter
   seam, or backward-compat handling.
3. Report only. Do NOT fix anything, do NOT commit.

## Report
Return ONLY this JSON:
{"findings": [{"description": "...", "file": "...", "severity": "high|medium|low"}], "dropped": ["finding + why not actionable"], "deviations": ["..."]}
