# Phase 1 — review

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need.

## Review skill
python-review

## Commit range
6133c8d9d9353ed4729d655bc890c97d4a577b5e..HEAD

## Task
1. Invoke the `python-review` skill (use the `Skill` tool) over the commit range above.
2. For each finding, decide if it's real and actionable for THIS change (Phase A —
   genericize the topic). Focus areas that matter here:
   - The field rename `is_mcp_related` → `is_relevant` is consistent; the only surviving
     old-name references are intentional backward-compat fallback reads (report filter,
     `_parse_response`, url_registry parquet-column compat) — flag any accidental leftover.
   - Prompt template stays `str.format`-safe (no stray literal `{`/`}`); topic variables
     are actually substituted.
   - Backward-compat reads genuinely handle old stored data without a migration.
   - No over-engineering: the repo follows MVP principles; extra abstractions are a
     finding, not a virtue.
3. Drop false positives, pre-existing issues, and anything about out-of-scope items
   (HTML templates still saying "MCP Monitor", report `min_relevance` plumbing, later
   phases) — those are deliberately deferred per the plan.
4. Report only. Do NOT fix anything, do NOT commit.

## Report
Return ONLY this JSON:
{"findings": [{"description": "...", "file": "...", "severity": "high|medium|low"}], "dropped": ["finding + why not actionable"], "deviations": ["..."]}

## Deviations from earlier steps
- phase 1 dev: Left src/html/duckdb-query-tool*.html references to is_mcp_related untouched — those files aren't in the brief's in-scope list and query historical parquet/frontmatter data that may still use the old column name.
- phase 1 dev: Applied 3 minor python-review cleanups beyond the literal brief text (deduped the is_relevant/is_mcp_related fallback into a private _is_relevant() helper in src/stages/report.py, fixed a stale 'MCP relevance score' docstring in src/models/url_registry.py, and added a comment explaining the anthropic_client is_mcp_related fallback) — all within already-in-scope files and consistent with the brief's backward-compat intent.
