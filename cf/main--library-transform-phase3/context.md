# Context — library-transform-phase3 (Source abstraction + Hacker News)

Shared reading for every step. The planner already explored the codebase; the file paths,
signatures, and decisions below are authoritative. Do not re-explore unless something here is
missing.

## What this run is
Plan **Phase C** of `plans/library_transformation_plan.md`. The cf runs are numbered but the
plan uses letters: phase-1 = plan Phase A, phase2 = plan Phase B, **this run = plan Phase C**.
Read the plan's "Phase C" bullet (lines ~56-64) for the intent.

Base commit for the whole run: `fd7c507` (end of Phase B). Baseline: **355 tests**,
`uv run poe check` green.

## Verification command
`uv run poe check` runs ruff check + ty check (parallel) then `pytest -q --tb=short`
(defined in `poe_tasks.toml`). All three must stay green. Run individual tests with
`uv run pytest tests/... -q`.

## Key files and current state

### `src/models/post.py` — the post model (`BlueskyPost`)
- `BlueskyPost(AnalyticsBase)` with: `id: str`, `author: str`, `content: str` (min_length 1,
  rejects whitespace-only), `created_at: datetime`, `links: list[HttpUrl]`, `tags: list[str]`
  (auto-extracted hashtags), `language: LanguageType` (auto-detected from content),
  `engagement_metrics: EngagementMetrics` (required: `likes`, `reposts`, `replies`, all `ge=0`),
  and optional thread fields (`thread_root_uri`, `thread_position`, `parent_post_uri`,
  `thread_depth`).
- There is **no `source` field yet** — Phase 1 adds `source: str = Field(default="bluesky", ...)`.
  The default doubles as the backward-compat read for old data (mirrors how Phase A handled the
  `is_mcp_related`→`is_relevant` rename via a fallback default).
- `EngagementMetrics(BaseModel)`: `likes`, `reposts`, `replies` (all int, `ge=0`).

### `src/stages/collect.py` — `CollectStage(InputStage)`
- `__init__` currently takes `settings`, `search_definition`, `max_posts`, `expand_urls`,
  `collect_threads`, thread params, `base_path`, `export_parquet`, `expand_references`,
  `max_reference_depth`. It constructs `self.bluesky_client = BlueskyClient(settings)`.
- `collect_posts(target_date)` (lines 57-107): checks `settings.has_bluesky_credentials`,
  then `async with self.bluesky_client as client: search_posts = await
  client.get_posts_by_definition(search_definition=..., max_posts=...)`, optionally does thread
  collection (`client.get_threads_for_posts`), URL expansion (`_expand_post_urls`), and
  reference expansion (`_expand_post_references`). Returns `list[BlueskyPost]`.
- `post_to_markdown(post, target_date)` (lines 266-297) builds frontmatter: `id`, `author`,
  `created_at`, `language`, `engagement`, `links`, `tags`, `stage`, `collected_at`, optional
  `thread`. **Phase 1 adds `"source": post.source` to this frontmatter.**
- `get_post_filename(post)` (lines 299-305): `post_{short_id}.md` where `short_id` is the last
  `/`-segment for `at://` ids, else the id verbatim. HN ids of the form `hn_<objectID>` produce
  `post_hn_<objectID>.md` — unique vs Bluesky rkeys, and the report lookup stays valid.
- `run_collection(target_date)` (lines 321-429): calls `collect_posts`, groups by
  `post.created_at.date()`, writes/updates markdown per post, exports parquet at the end.

### `src/bluesky/client.py` — `BlueskyClient`
- Async context manager (`__aenter__`/`__aexit__`), authenticates on enter.
- `get_posts_by_definition(search_definition, max_posts) -> list[BlueskyPost]` (line 257) is the
  search entry point the collect stage uses. `search_by_definition`, `get_threads_for_posts`,
  `get_post_by_uri`, `get_thread_by_uri` also exist. `_convert_post_to_model` builds a
  `BlueskyPost` from API data — this is where `source="bluesky"` is naturally set (or rely on the
  field default).
- `settings.has_bluesky_credentials` gates whether Bluesky can run.

### `src/config/collection.py` — `CollectionConfig`
- Pydantic model: `name`, `topic: TopicConfig`, `ui: UIConfig`, `evaluation: EvaluationSelection`,
  `searches: SearchConfig`, `default_search: str`. Properties `stages_base = stages/<name>`,
  `output_base = output/<name>`. Validator ensures `default_search` exists and is enabled.
- `load_collection(name, config_dir="config")` reads `config/collections/<name>.yaml`.
- **Phase 2 adds** `sources: list[str] = Field(default_factory=lambda: ["bluesky"])`. Consider a
  validator rejecting unknown source names against the known set `{"bluesky", "hackernews"}`.

### `src/config/searches.py` — `SearchDefinition`
- Fields: `name`, `include_terms: list[str]` (required, non-empty), `exclude_terms: list[str]`,
  `sort: str` (default "latest"), `query_syntax: str` (validated set). HN query mapping uses
  `" ".join(include_terms)`; `exclude_terms` ignored for HN (MVP).

### `config/collections/mcp.yaml` and `duckdb.yaml`
- `mcp.yaml`: `default_search: mcp_tag`, embeds several searches. **Stays Bluesky-only.** After
  Phase 2, it may either omit `sources:` (defaults to `["bluesky"]`) or state it explicitly —
  either way its behavior must not change.
- `duckdb.yaml`: second topic (DuckDB). **Phase 2 sets its `sources: [bluesky, hackernews]`** as
  the proof that HN flows through the pipeline. DuckDB is well represented on HN.
- There is a parity test `test_mcp_matches_base_app_config` in
  `tests/test_config/test_collection.py` asserting mcp collection == `config/base/app.yaml` for
  topic/ui/evaluation/searches. Adding a `sources` default must not break it (the base app config
  has no `sources`; keep the field defaulted and don't assert it in that test unless base config
  is updated in lockstep — prefer leaving base untouched).

### `src/cli/stage_commands.py` — CLI wiring
- `load_collection_or_exit(name)` (line 37) loads a collection or exits cleanly.
- `collect(...)` (line 72): resolves `search_key`, **exits early if `settings.has_bluesky_credentials`
  is false** (lines 131-136). Phase 2 must relax this so the check only fires when `bluesky` is in
  `collection.sources`. Then constructs `CollectStage(settings=..., search_definition=...,
  ..., base_path=collection.stages_base)` (line 153) and runs it. **Phase 2 threads
  `collection.sources` into `CollectStage`.**
- Same `run_all` flow invokes collect; keep it working.

### `src/stages/report.py` — `ReportStage`
- Builds articles by reading evaluate-stage markdown, then **looking up the original collect post
  markdown** to get `author`/`created_at` (two near-duplicate blocks: ~lines 158-284 and
  ~315-425 — both must be updated in Phase 3). The lookup loads `post_<id>.md` and calls
  `post_md.get_frontmatter_value("author", "unknown")` etc. **Phase 3 reads
  `post_md.get_frontmatter_value("source", "bluesky")` in the same place** and passes it into the
  `eval_dict`/`ReportArticle`.
- `_is_relevant(evaluation)` shows the established fallback-default pattern for renamed/added fields.

### `src/models/report.py` — `ReportArticle`
- Fields include `url`, `title`, `perex`, `post_id`, `bluesky_url: HttpUrl`, `author`,
  `timestamp`, `created_at`, `relevance_score`, `domain`, `content_type`, `language`,
  `debug_filename`. **Phase 3 adds `source: str = "bluesky"`.**
- `from_post_and_evaluation(post_id, author, created_at, evaluation, debug_filename)` (line 35)
  builds `bluesky_url = f"https://bsky.app/profile/{author}/post/{actual_post_id}"`. **Phase 3
  makes this source-aware**: add a `source` param; for `hackernews` build the permalink
  `https://news.ycombinator.com/item?id=<objectID>` (strip the `hn_` prefix from post_id) instead
  of a bsky.app URL. Keep the field name `bluesky_url` (renaming is Phase D) — accepted misnomer.

### `src/templates/daily.html` — article card
- Lines 8-26 loop articles; line 16 renders `via <a href="{{ article.bluesky_url }}">{{
  article.author }}</a>` then `at {{ article.timestamp }} • {{ article.domain }}`. **Phase 3 adds
  a source badge here** (e.g. append `• {{ article.source_label }}` or a small styled span).
  Keep it minimal and consistent with the existing `•`-separated meta line. `homepage.html` also
  lists items — check whether it renders per-article meta and add the badge there too if so.

## Hacker News (Algolia) API — reference for Phase 2
- Free, no auth, JSON. Endpoint for recent stories:
  `https://hn.algolia.com/api/v1/search_by_date?query=<terms>&tags=story&hitsPerPage=<n>`
  (use `search_by_date` for recency, matching Bluesky's "latest" default; `search` ranks by
  relevance/points if preferred).
- Response: `{"hits": [ { "objectID": "12345", "title": "...", "url": "https://..." | null,
  "author": "pg", "points": 42, "num_comments": 17, "created_at_i": 1699999999,
  "created_at": "2024-..." }, ... ]}`. `url` can be null (Ask HN / text posts).
- Map each hit → `BlueskyPost`:
  - `id = f"hn_{objectID}"`
  - `author = hit["author"]`
  - `content = hit["title"]` (non-empty; skip hits with empty title)
  - `created_at = datetime.fromtimestamp(hit["created_at_i"], tz=UTC)`
  - `links = [HttpUrl(hit["url"])]` when `url` is set, else `[]`
  - `engagement_metrics = EngagementMetrics(likes=hit.get("points") or 0, reposts=0,
    replies=hit.get("num_comments") or 0)`
  - `source = "hackernews"`
- Use `httpx` (already a dependency, `httpx>=0.25.0`) with an async client. No credentials.
- Handle request errors gracefully (log + return `[]`), mirroring `collect_posts`'s
  exception-swallowing style, so one source failing doesn't kill the run.

## Design decisions (do not relitigate)
- `Source` is a **Protocol** (or minimal ABC) in `src/sources/base.py` exposing
  `async def search(self, search_definition: SearchDefinition, max_posts: int) ->
  list[BlueskyPost]` and a `name` attribute. Keep it tiny; no lifecycle/close methods unless a
  source genuinely needs them (Bluesky's client is a context manager — manage that inside
  `BlueskySource.search`).
- `BlueskySource` wraps `BlueskyClient` and performs only the **search** call; thread/URL/reference
  expansion stays in `CollectStage` and runs only for Bluesky posts (guard on `post.source ==
  "bluesky"` or on which source produced them). Do NOT move expansion into the source this run.
- Collections list sources as a plain name list; per-source params deferred.
- `BlueskyPost` and `bluesky_url` keep their names this run; renaming is Phase D.
- Auxiliary output (about/stats/publish) stays out of scope.

## MVP guardrails (project CLAUDE.md)
Minimal implementation, no speculative abstractions, working over perfect, skip edge cases unless
required, neutral commit messages with the Claude Code footer, `git add -A`, never `--no-verify`,
never push. The `python-review` skill runs on changed Python before done.

## Prior-run deviations worth knowing (from Phase B log)
- Phase B dropped the `--config` search-override from `collect`/`run_all` (searches come solely
  from the collection). Don't reintroduce it.
- `EvaluationSelection` uses a Field alias (`model_config_name` ← YAML `model_config`) because
  `model_config` is reserved on pydantic BaseModel.
- Phase B added a `load_collection_or_exit` helper and made unknown-collection a clean CLI error.
- `render_about` still renders default branding (out of scope). `topic.min_relevance_score`
  remains unwired. Leave both alone.
- cf orchestration files are committed alongside code (`git add -A` per project convention);
  that's expected, not a scope violation.
