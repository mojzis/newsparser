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
