# Phase 3 — dev

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need. Phases 1–2 delivered the Collection model and wired it through CLI/stages/evaluator with namespaced paths.

## Task
Brand each collection's generated site from its own `ui` config instead of hardcoded "MCP".

1. Thread `site_title` and `site_tagline` from `collection.ui` into `ReportGenerator`
   (`src/reports/generator.py`): store them on the instance (constructor args with sensible
   defaults) and add them to the render context of every `template.render(...)` call
   (daily report, homepage, and any other). `ReportStage` should construct
   `ReportGenerator` with the collection's `ui.site_title` / `ui.site_tagline`.
2. Templatize the hardcoded branding strings in `src/templates/` to use the context vars
   with defaults, per context.md:
   - `base.html`: `<title>` block and the "Bluesky MCP Monitor" nav link.
   - `homepage.html`: header line and tagline block.
   - `about.html`: title.
   - `daily.html`: the two "MCP Monitor" occurrences.
   Use `{{ site_title | default('MCP Monitor') }}` and
   `{{ site_tagline | default('Daily digest of Model Context Protocol mentions') }}` so a
   render without the vars still produces the current output. Keep `theme` out of scope.
3. Ensure any template that renders these vars actually receives them (add to the relevant
   render contexts; if a template extends `base.html`, the child render must pass the vars).

## In-scope files
- `src/reports/generator.py`
- `src/stages/report.py` (only to pass ui into `ReportGenerator`, if not already)
- `src/templates/base.html`, `homepage.html`, `about.html`, `daily.html`
- Tests as needed under `tests/test_reports/`

## Out of scope
- `theme` support / swappable stylesheets.
- Namespacing auxiliary output (stats/about/publish).
- Any topic/relevance-score logic.

## Mode
Unconstrained delivery. Make it work and clean enough to commit. Don't worry about review nits — that belongs to the review step.

## Contract
- Run `uv run poe check` green before committing — no pre-commit hooks exist.
- Prove branding swaps without network: render a report/homepage for the `duckdb`
  collection (e.g. via a small `uv run python` snippet constructing `ReportGenerator` with
  duckdb's ui and rendering, or an offline unit test) and confirm the output HTML contains
  the duckdb `site_title` and not "MCP Monitor"; confirm the default (no ui) render still
  says "MCP Monitor".
- Finish by running `git commit` (`git add -A`; footer `🤖 Generated with [Claude Code](https://claude.ai/code)`).
- If checks fail, fix and re-commit until clean. Multiple commits OK. No `--no-verify`. Do NOT push.

## Report
Return ONLY this JSON:
{"commit_shas": ["..."], "summary": "one sentence", "deviations": ["..."], "unresolved_issues": ["..."]}

## Deviations from earlier steps
- phase 1 dev: EvaluationSelection uses a Field alias (model_config_name -> YAML key model_config) with populate_by_name=True, per context.md's suggested approach.
- phase 1 dev: Committed the untracked cf/ orchestration files alongside the code changes since the brief specifies `git add -A`.
