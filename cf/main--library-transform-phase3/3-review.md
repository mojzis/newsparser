# Phase 3 — review

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need.

## Review skill
python-review

## Commit range
<base sha for this phase — provided by orchestrator; overall plan base is fd7c507>..HEAD

## Task
1. Invoke the review skill (use the `Skill` tool) over the commit range.
2. For each finding, decide if it's real and actionable. Drop false positives and pre-existing
   issues. Keep MVP scope in mind: keeping the `bluesky_url` field name (now holding the source
   permalink) is a deliberate documented deferral to Phase D, and no per-source report sections are
   expected. Do scrutinize: the source read + default in both report lookup blocks (they are
   near-duplicated — check both were updated consistently), the HN permalink construction (prefix
   stripping, objectID correctness), and template escaping/consistency of the badge. Since Phase B's
   review caught a silently-changed default-collection string, check the `mcp` report output did not
   drift beyond the intended added badge.
3. Report only. Do NOT fix anything, do NOT commit.

## Report
Return ONLY this JSON:
{"findings": [{"description": "...", "file": "...", "severity": "high|medium|low"}], "dropped": ["finding + why not actionable"], "deviations": ["..."]}

## Deviations from earlier steps
- phase 1 dev: Wired BlueskySource with an optional injected client (defaulting to owning its own when none given) so CollectStage reuses one authenticated Bluesky session instead of logging in twice per collect run; flagged by python-review as a should-fix and addressed within scope.

## Deviations from earlier steps
- phase 1 check: Confirmed the phase 1 dev deviation (BlueskySource optional injected client) is in-scope and correctly wired; no code changes made by check.
