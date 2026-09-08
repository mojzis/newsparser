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
- phase 2 dev: Dropped the --config/config_path search-config override from collect and run_all in both stage_commands.py and new_commands.py (searches are now sourced solely from the loaded collection); legacy onsp commands in src/cli/legacy_commands.py still keep --config unchanged since they're out of scope.
- phase 2 dev: Added a small load_collection_or_exit helper in stage_commands.py so status/list_files/clean surface an unknown --collection as a clean CLI error (exit 1) instead of an unhandled FileNotFoundError traceback; collect/fetch/evaluate/report already had a wrapping try/except so load_collection is called directly there.
- phase 2 dev: Added new test files (tests/test_evaluation/test_anthropic_client.py, tests/test_stages/test_report_stage.py, tests/test_cli/test_stage_commands.py) beyond the explicitly named in-scope files, per the brief's allowance to extend tests as needed for collection-aware paths/evaluator.
- phase 3 dev: Dropped the literal 'Bluesky ' prefix from base.html's nav-brand link, replacing the whole link text with the site_title default filter.
- phase 3 dev: Added a ui: UIConfig | None constructor param to ReportStage (defaulting to UIConfig()) to receive collection.ui and pass it through to ReportGenerator.
- phase 3 dev: Extracted a private ReportGenerator._base_context() helper so all three template.render(...) call sites build the site_title/site_tagline context consistently.
- phase 3 dev: Added tests beyond the explicitly named files (test_generate_daily_report_custom_branding, test_generate_homepage_custom_branding, test_run_report_uses_collection_ui_branding).
- phase 3 dev: render_about still renders about.html through its own bare Jinja Environment without passing site_title, so it always shows default 'MCP Monitor' branding regardless of collection -- left as-is, out of scope.

## Additional verification (post-review fixes)
Verify each of these findings was addressed:
- The mcp collection's homepage tagline reproduces the original "Daily digest of Model Context Protocol discussions from Bluesky" text exactly (either by updating mcp.yaml's site_tagline/the default, or by confirming the change was intentionally accepted with a documented reason).
