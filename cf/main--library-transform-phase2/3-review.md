# Phase 3 — review

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need.

## Review skill
python-review

## Commit range
Use the base sha the orchestrator gives you for this phase..HEAD (the Phase 3 dev commits).

## Task
1. Invoke the review skill (use the `Skill` tool) over the commit range.
2. For each finding, decide if it's real and actionable. Drop false positives and
   pre-existing issues.
3. Report only. Do NOT fix anything, do NOT commit.

## Focus notes for this phase
- Mostly Python render-context plumbing + Jinja template edits. Watch for: render calls
  that reference `site_title`/`site_tagline` but don't actually receive them (would fall to
  default and silently mis-brand), autoescape correctness, and child templates that extend
  `base.html` without passing the vars through.
- Confirm the default fallback genuinely reproduces prior output (no accidental behavior
  change for the mcp collection).
- Do NOT flag deferred items: `theme`/stylesheet swapping and auxiliary-output namespacing.

## Report
Return ONLY this JSON:
{"findings": [{"description": "...", "file": "...", "severity": "high|medium|low"}], "dropped": ["finding + why not actionable"], "deviations": ["..."]}
