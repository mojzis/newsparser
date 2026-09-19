# Learnings: library-transform-phase3

## What worked
- Planner correctly cross-referenced the prior cf phase2 run's log to inherit its deviations (dropped --config override, EvaluationSelection alias, load_collection_or_exit, render_about gap) into context.md, so phase3 dev/check/review agents never re-litigated already-settled decisions.
- Each phase's single review-round fix loop (phase 1: misleading test name; phase 2: misleading test name) resolved cleanly on the first fix + re-check pass — no second escalation needed.
- Deviation propagation to not-yet-run briefs worked as designed: later dev/check/review agents cited and confirmed earlier deviations (e.g. BlueskySource's injected client, the shared sources/registry.py) instead of flagging them as surprises.

## Friction
- Two low-severity review findings in a row (phase 1 and phase 2) were the same class of bug: a test name/docstring claiming to verify behavior that the implementation doesn't actually perform (source-stamping, client-skipping). Might be worth a planner-side note to dev agents to double check test names match assertions before returning.
- Phase 3 dev surfaced two unresolved_issues (bluesky_url misnomer, duplicated report.py lookup blocks) that review then re-flagged and re-dropped as the same already-logged deferrals — slight duplication of reasoning across dev report and review report, though harmless.

## Suggestions for cml/SKILL.md
- Consider a "before returning, sanity check your test names against their assertions" line in cml-dev's own instructions, since this exact defect recurred twice back-to-back.
