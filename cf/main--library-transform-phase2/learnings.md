# Learnings: library-transform-phase2

## What worked
- Passing phase-1's deviations log forward (via cf log check) let the planner correctly map "phase 2" to the plan's Phase B and know to skip the unwired `topic.min_relevance_score` thread.
- Every one of the 3 phases needed exactly one review-fix-recheck round — findings were real but low severity (test coverage gap, error-handling inconsistency, a silently-changed tagline string) and each was fixed cleanly on the first attempt.
- The phase-3 review agent caught a genuine regression (mcp collection's homepage tagline text drifted from "...discussions from Bluesky" to "...mentions" during templatization) that check's offline-render verification didn't surface, because check only tested the *default* fallback path and the *duckdb* branded path, not whether *mcp*'s own branded output matched the pre-refactor original byte-for-byte.

## Friction
- Dev agents routinely made judgment calls beyond the brief's literal scope (e.g. adding a `load_collection_or_exit` helper, extracting `_base_context()`, dropping `--config` override) — all reasonable and documented as deviations, but this pushed real design decisions onto sonnet dev agents rather than the opus planner. None caused problems here, but a stricter brief could pre-empt some review-round churn.
- Deviation propagation to not-yet-run briefs is mechanically expensive at haiku effort (many near-identical Edit/Bash appends across 5-8 files per phase). Consider a lighter mechanism (e.g. a single running deviations.md that check/review agents are told to read instead of duplicating text into every brief).

## Suggestions for cml/SKILL.md
- Consider explicitly telling the check agent, when the phase's dev deviations mention changing user-visible strings/behavior for the *default* collection, to diff the new output against the pre-refactor original (not just against the new default fallback) — this would have caught the mcp tagline regression one round earlier.
- The "append deviations to every not-yet-run brief" step could be simplified to "append deviations to a single deviations.md and reference it from every brief's context.md include" to cut down on repetitive file edits.
