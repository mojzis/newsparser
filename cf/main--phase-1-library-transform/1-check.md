# Phase 1 — check

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need.

## Verifies
Phase A deliverable: the topic is now configuration-driven, the prompt is parameterized,
the relevance field is renamed `is_relevant` with backward-compat reads of the old
`is_mcp_related` key, and the default MCP config still behaves identically. No stray
un-renamed references, and the build is green.

## Verification steps
1. Run `uv run poe check` (ruff + ty + pytest). All three must pass. Paste the summary.
2. Confirm config: `config/base/app.yaml` has a `topic` section with `name`,
   `description`, `min_relevance_score`; `TopicConfig` exists in
   `src/config/config_manager.py` and `AppConfig` has a `topic` field. Run
   `uv run nsp validate-config` (or `uv run onsp validate-config`) — should succeed.
3. Confirm the prompt: `config/base/prompts.yaml` template no longer hardcodes the MCP
   definition, uses `{topic_name}` / `{topic_description}`, and instructs `is_relevant`
   output; the two variables are registered in the `variables:` list.
4. Prompt renders with the topic substituted and no leftover placeholder. Without calling
   the Anthropic API, render the prompt (see context.md "How to verify" — constructing
   `AnthropicEvaluator` builds the client but makes no network call; or render the loaded
   template + topic config directly). Assert the output contains the topic name text and
   contains no unfilled `{topic_` substring.
5. Field rename is complete: `grep -rn "is_mcp_related" src/` returns only the documented
   backward-compat fallback reads (report.py filter fallback, anthropic_client
   `_parse_response` fallback, utils/url_registry parquet-column compat). No producer code
   should still write `is_mcp_related` as the primary key. `ArticleEvaluation` and
   `URLEntry` expose `is_relevant`.
6. Backward-compat read works: confirm `src/stages/report.py` filters read
   `is_relevant` with an `is_mcp_related` fallback, and `src/utils/url_registry.py`
   copies an old `is_mcp_related` column to `is_relevant` when loading old parquet.

## Pass condition
`uv run poe check` passes; config and prompt are parameterized as above; the prompt
renders with the topic substituted and no unfilled placeholder; the only remaining
`is_mcp_related` references in `src/` are the documented fallbacks; `validate-config`
succeeds.

## Constraints
- Read-only. Do NOT modify code or commit. If the deliverable is broken, report it —
  do not fix it. Do NOT make live Anthropic API calls (would need `ANTHROPIC_API_KEY`
  and is out of scope for this check).

## Report
Return ONLY this JSON:
{"verified": true, "evidence": "what you observed (paste output)", "deviations": ["..."], "issues": ["..."]}

## Deviations from earlier steps
- phase 1 dev: Left src/html/duckdb-query-tool*.html references to is_mcp_related untouched — those files aren't in the brief's in-scope list and query historical parquet/frontmatter data that may still use the old column name.
- phase 1 dev: Applied 3 minor python-review cleanups beyond the literal brief text (deduped the is_relevant/is_mcp_related fallback into a private _is_relevant() helper in src/stages/report.py, fixed a stale 'MCP relevance score' docstring in src/models/url_registry.py, and added a comment explaining the anthropic_client is_mcp_related fallback) — all within already-in-scope files and consistent with the brief's backward-compat intent.

## Additional verification (post-review fixes)
Verify each of these findings was addressed:
- Prompt genericization is incomplete: in config/base/prompts.yaml the relevance_score instruction line still hardcodes the topic — `2. relevance_score (0.0-1.0): How relevant is this to {topic_name}? 0=unrelated, 1=directly about MCP`. Fix: `1=directly about {topic_name}`.
- Newly-added comment in src/evaluation/anthropic_client.py (~line 178) justifies the is_mcp_related fallback with an inaccurate rationale about prompt caching. Fix: correct or remove the misleading explanation.
