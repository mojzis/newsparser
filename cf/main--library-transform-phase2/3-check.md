# Phase 3 — check

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need.

## Verifies
Generated site branding comes from the collection's `ui` config: `site_title`/`site_tagline`
flow into the report/homepage/daily render contexts, the hardcoded "MCP Monitor" strings in
the templates are templatized with safe defaults, and the `duckdb` collection produces a
correctly-branded, separate site while the default still reads "MCP Monitor".

## Verification steps
1. `uv run poe check` — ruff clean, ty clean, full pytest green. Paste the tail.
2. `grep -rn "MCP Monitor\|Bluesky MCP Monitor" src/templates/` — remaining occurrences
   should only be inside `default(...)` filters, not bare hardcoded text.
3. Confirm `ReportGenerator` accepts/holds `site_title`/`site_tagline` and includes them in
   every `template.render(...)` context, and that `ReportStage` passes the collection's ui.
4. Branding swap (offline): render the homepage/daily template with the `duckdb` collection
   ui (via a `uv run python` snippet or the phase's unit test) and confirm the HTML contains
   the duckdb site title/tagline and NOT "MCP Monitor". Then render with no ui vars and
   confirm it still contains "MCP Monitor" (default fallback intact).
5. `git show --stat HEAD` (and earlier phase-3 commits) touch only in-scope files.

## Pass condition
`poe check` green; no bare hardcoded "MCP Monitor" left in templates (only as defaults);
duckdb render is branded from its ui; default render unchanged.

## Constraints
- Read-only. Do NOT modify code or commit. Do NOT call external APIs. If broken, report it — do not fix it.

## Report
Return ONLY this JSON:
{"verified": true, "evidence": "what you observed (paste output)", "deviations": ["..."], "issues": ["..."]}

## Deviations from earlier steps
- phase 1 dev: EvaluationSelection uses a Field alias (model_config_name -> YAML key model_config) with populate_by_name=True, per context.md's suggested approach.
- phase 1 dev: Committed the untracked cf/ orchestration files alongside the code changes since the brief specifies `git add -A`.
