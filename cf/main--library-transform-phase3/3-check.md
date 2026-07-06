# Phase 3 — check

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need.

## Verifies
The daily report shows a per-article source badge, `source` is threaded from collect-stage post
frontmatter into `ReportArticle`, and the "via" permalink is source-appropriate (bsky.app for
Bluesky, news.ycombinator.com for HN). The `mcp` report still shows "Bluesky".

## Verification steps
1. `uv run poe check` — ruff + ty green, pytest green (count ≥ Phase 2's). Paste the tail.
2. Confirm `ReportArticle` has a `source` field (default `"bluesky"`) and that
   `from_post_and_evaluation` builds the HN permalink `https://news.ycombinator.com/item?id=<id>`
   for `source="hackernews"` (hn_ prefix stripped) and the bsky.app URL for `source="bluesky"`.
   Verify via the unit tests or an offline snippet.
3. Confirm both post-lookup blocks in `src/stages/report.py` read `source` from post frontmatter
   with a `"bluesky"` default and pass it through.
4. Render check: build a report (via existing tests or an offline render snippet) with a mix of a
   Bluesky and a Hacker News article and confirm the rendered daily HTML contains a source badge per
   article, showing "Bluesky" and "Hacker News" (or the chosen labels). Confirm a Bluesky-only
   report still shows "Bluesky" and the mcp branding/layout is otherwise unchanged.
5. `git show --stat HEAD` (and sibling phase-3 commits) touch only in-scope files (+ cf/ docs).

## Pass condition
`poe check` green; `source` on `ReportArticle` with correct default; source-aware permalink;
per-article badge rendered; mcp report unchanged apart from the added badge.

## Constraints
- Read-only. Do NOT modify code or commit. If the deliverable is broken, report it — do not fix it.

## Report
Return ONLY this JSON:
{"verified": true, "evidence": "what you observed (paste output)", "deviations": ["..."], "issues": ["..."]}

## Deviations from earlier steps
- phase 1 dev: Wired BlueskySource with an optional injected client (defaulting to owning its own when none given) so CollectStage reuses one authenticated Bluesky session instead of logging in twice per collect run; flagged by python-review as a should-fix and addressed within scope.

## Deviations from earlier steps
- phase 1 check: Confirmed the phase 1 dev deviation (BlueskySource optional injected client) is in-scope and correctly wired; no code changes made by check.

## Deviations from earlier steps
- phase 2 dev: Factored a shared src/sources/registry.py (SOURCE_FACTORIES/KNOWN_SOURCES) used by both CollectStage._build_sources and CollectionConfig source validator, to avoid duplicating the known-source set; added after python-review flagged duplication as a should-fix, within the brief in-scope files.
