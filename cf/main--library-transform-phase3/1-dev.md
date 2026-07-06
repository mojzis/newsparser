# Phase 1 — dev

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need.

## Task
Introduce a minimal `Source` abstraction and stamp a `source` field on every collected post,
without changing the `mcp` pipeline's behavior. This is a refactor + additive field only.

1. Add `source: str = Field(default="bluesky", ...)` to `BlueskyPost` in `src/models/post.py`.
   The default is also the backward-compat read for old stored data (frontmatter/parquet lacking
   the field).
2. Create `src/sources/` package:
   - `src/sources/base.py`: a minimal `Source` protocol (or small ABC) with a `name` attribute
     and `async def search(self, search_definition: SearchDefinition, max_posts: int) ->
     list[BlueskyPost]`. Keep it tiny — no close/lifecycle methods.
   - `src/sources/bluesky.py`: `BlueskySource` implementing the protocol. It wraps
     `BlueskyClient` and performs only the **search** call
     (`get_posts_by_definition`), managing the client's async context internally, and ensures the
     returned posts carry `source="bluesky"` (either set explicitly in `_convert_post_to_model` or
     rely on the field default).
3. Rewire `CollectStage.collect_posts` (`src/stages/collect.py`) to obtain search results through a
   `BlueskySource` instead of calling `self.bluesky_client.get_posts_by_definition` directly. Keep
   the existing thread/URL/reference expansion in `CollectStage` unchanged (it still uses
   `self.bluesky_client` for `get_threads_for_posts`, references, etc.). The credential check stays.
4. Add `"source": post.source` to the frontmatter in `CollectStage.post_to_markdown`.
5. Tests: add/adjust unit tests proving the `source` field defaults to `"bluesky"`, that
   `BlueskySource` returns Bluesky-stamped posts, and that collect frontmatter includes `source`.

## In-scope files
- `src/models/post.py`
- `src/sources/__init__.py`, `src/sources/base.py`, `src/sources/bluesky.py` (new)
- `src/stages/collect.py`
- `tests/` (new/updated tests as needed — e.g. `tests/test_sources/`, existing post/collect tests)

## Out of scope
- Hacker News, the `sources:` collection config field, collect dispatch over multiple sources
  (Phase 2).
- Report source badge (Phase 3).
- Moving thread/URL/reference expansion into the source — keep it in `CollectStage`.
- Renaming `BlueskyPost` (Phase D). Auxiliary output. `render_about`.

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
