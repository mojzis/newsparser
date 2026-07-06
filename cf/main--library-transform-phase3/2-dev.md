# Phase 2 — dev

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need.

## Task
Add Hacker News as a second source and let a collection draw from multiple sources.

1. `src/sources/hackernews.py`: `HackerNewsSource` implementing the `Source` protocol from Phase 1.
   - `async def search(self, search_definition, max_posts) -> list[BlueskyPost]` queries the Algolia
     API `https://hn.algolia.com/api/v1/search_by_date?query=<terms>&tags=story&hitsPerPage=<max_posts>`
     with `httpx` (async, no auth). `<terms>` = `" ".join(search_definition.include_terms)`;
     `exclude_terms` are ignored (MVP — document).
   - Map each hit to `BlueskyPost` per the mapping in context.md (`id=f"hn_{objectID}"`,
     `content=title`, `author`, `created_at` from `created_at_i` in UTC, `links=[url]` when present
     else `[]`, `engagement_metrics` from `points`/`num_comments`, `source="hackernews"`). Skip hits
     with empty titles (content must be non-empty).
   - On request/parse error: log and return `[]` (don't crash the run).
2. `src/config/collection.py`: add `sources: list[str] = Field(default_factory=lambda: ["bluesky"])`
   to `CollectionConfig`. Optionally add a validator rejecting names outside `{"bluesky",
   "hackernews"}` with a clear error. Keep the `mcp`/base-config parity test green (do not force a
   `sources` key into `config/base/app.yaml`).
3. `src/stages/collect.py`: `CollectStage` should accept the collection's source names (e.g. a
   `sources: list[str]` constructor param, default `["bluesky"]`), build the corresponding `Source`
   instances (a small name→Source factory; Bluesky needs `settings`, HN needs nothing), and in
   `collect_posts` iterate all configured sources, aggregating their posts. Bluesky-only
   post-processing (thread collection, URL expansion, reference expansion) must run **only** on
   Bluesky-sourced posts — partition by `post.source` (or apply per-source) so HN posts pass through
   untouched. The Bluesky credential check must fire only when `bluesky` is among the sources.
4. `src/cli/stage_commands.py`: thread `collection.sources` into `CollectStage`; relax the
   `has_bluesky_credentials` early-exit (lines ~131-136) so it only triggers when `bluesky` is a
   configured source. Keep `run_all` working.
5. `config/collections/duckdb.yaml`: set `sources: [bluesky, hackernews]` as the proof. Leave
   `mcp.yaml` Bluesky-only (omit `sources` to use the default, or set `[bluesky]` explicitly).
6. Tests: `HackerNewsSource` mapping (mock the httpx response — do NOT hit the network in tests),
   the `sources` config field + validator, and `CollectStage` dispatching over multiple sources with
   Bluesky-only expansion isolation.

## In-scope files
- `src/sources/hackernews.py` (new), `src/sources/__init__.py`
- `src/config/collection.py`
- `src/stages/collect.py`
- `src/cli/stage_commands.py`
- `config/collections/duckdb.yaml` (and `mcp.yaml` only if making `sources` explicit)
- `tests/` (mocked HN response, config, dispatch tests)

## Out of scope
- Report source badge (Phase 3).
- RSS / other sources; per-source search-parameter customization (deferred).
- Moving Bluesky expansion into `BlueskySource`; renaming `BlueskyPost`.
- Real network calls in tests. Auxiliary output / `render_about`.

## Mode
Unconstrained delivery. Make it work and clean enough to commit. Don't worry about review nits — that belongs to the review step.

## Contract
- Finish by running `git commit` so pre-commit hooks execute.
- If hooks fail, address findings and re-commit until clean.
- Multiple commits OK. Do NOT skip hooks (no `--no-verify`). Do NOT push.
- Run `uv run poe check` before committing; it must be green (ruff + ty + full pytest).

## Report
Return ONLY this JSON:
{"commit_shas": ["..."], "summary": "one sentence", "deviations": ["..."], "unresolved_issues": ["..."]}
