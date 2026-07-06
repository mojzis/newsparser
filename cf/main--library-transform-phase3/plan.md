# cml plan: library-transform-phase3 (Source abstraction + Hacker News / Phase C)

- **Branch**: main
- **Review skill**: python-review
- **Phase count**: 3

## Context
This is **Phase C** ("Source abstraction + second source") of
`plans/library_transformation_plan.md`. The cf runs are numbered while the library plan
uses letters: `cf/main--phase-1-library-transform/` = plan **Phase A** (genericize the
topic), `cf/main--library-transform-phase2/` = plan **Phase B** (collections), and this
run = plan **Phase C**.

Phase B (base commit `fd7c507`) shipped: a `CollectionConfig` model
(`src/config/collection.py`) bundling topic + ui + evaluation + searches + `default_search`
with namespaced `stages_base`/`output_base`; a `--collection` flag (default `mcp`) threaded
through every stage CLI command and the collect/evaluate/report stages; and per-collection
site branding. Two collections exist: `config/collections/mcp.yaml` (reproduces today's
behavior) and `config/collections/duckdb.yaml` (proof of a second topic). Baseline is
**355 tests**, `uv run poe check` green (ruff + ty + pytest).

Today the only source is Bluesky, wired directly into `CollectStage`
(`src/stages/collect.py`) via `BlueskyClient`. Phase C introduces a minimal `Source`
abstraction, stamps a `source` field on every collected post, adds **Hacker News (Algolia
API)** as the second source, lets a collection list which sources it draws from, and shows a
per-item source badge in the report.

Constraints: MVP methodology (project CLAUDE.md) — minimal implementation, no speculative
abstractions, working over perfect. `stages/`, `output/`, `data/` are gitignored and there
is no local data, so new fields/paths orphan nothing and need no migration. Backward compat
for the `mcp` collection must hold: it stays Bluesky-only and its output must not change.

## Final deliverable
A minimal `Source` protocol (`src/sources/`) with the existing Bluesky collector refactored
into a `BlueskySource` and a new `HackerNewsSource` (Algolia API, no auth). Every collected
post carries a `source` field (default `"bluesky"`). A collection's YAML lists the sources it
draws from (`sources:`, default `["bluesky"]`); `CollectStage` iterates the configured
sources and aggregates their posts, applying Bluesky-only post-processing (thread/URL/
reference expansion) solely to Bluesky posts. The daily report shows a per-item source badge.
Proof: a collection configured with `[bluesky, hackernews]` collects Hacker News stories into
the pipeline and renders them with a "Hacker News" badge, while the `mcp` collection stays
Bluesky-only and unchanged.

## Success criteria
- `BlueskyPost` gains `source: str = "bluesky"`; collect-stage frontmatter records it; old
  stored data without the field reads back as `"bluesky"`.
- `src/sources/` exposes a `Source` protocol, `BlueskySource`, and (phase 2) `HackerNewsSource`.
- The `mcp` collection's collect output is byte-equivalent to before (still Bluesky-only,
  `source: bluesky` added to frontmatter is the only intended change).
- A collection listing `hackernews` collects real HN stories mapped to the post model with
  `source: "hackernews"`, unique filenames, no Bluesky-credential requirement when Bluesky
  isn't among its sources.
- The daily report renders a source badge per article; `mcp` articles show "Bluesky".
- `uv run poe check` stays green throughout (ruff + ty + full pytest suite).

## Phase 1: Source protocol + `source` field (Bluesky as a Source)
**Deliverable**: A new `src/sources/` package with a minimal `Source` protocol and a
`BlueskySource` adapter wrapping the existing search path; a `source: str = "bluesky"` field
on `BlueskyPost`; `CollectStage` obtains search results through `BlueskySource` and records
`source` in frontmatter. Pure refactor + additive field — the `mcp` pipeline behaves
identically. No Hacker News, no config changes yet.
**Steps**: dev, check, review

## Phase 2: Hacker News source + collection `sources` config + collect dispatch
**Deliverable**: `HackerNewsSource` (Algolia `search_by_date` API) mapping HN stories to the
post model with `source: "hackernews"`; a `sources: list[str]` field on `CollectionConfig`
(default `["bluesky"]`); `CollectStage` builds source instances from the collection and
aggregates their posts, running Bluesky-only expansion only on Bluesky posts and requiring
Bluesky credentials only when Bluesky is a configured source; `duckdb.yaml` updated to
`[bluesky, hackernews]` as the proof.
**Steps**: dev, check, review

## Phase 3: Per-item source badge in the report
**Deliverable**: `source` threaded from collect-stage post frontmatter through the report
lookup into a `source` field on `ReportArticle`; the daily template renders a per-article
source badge (human label, e.g. "Bluesky" / "Hacker News"); the "via" permalink is built
source-appropriately so HN items link to their HN item page rather than a bogus bsky.app URL.
**Steps**: dev, check, review

## Notes
- **Post model name**: the model stays `BlueskyPost` this run; renaming it to a generic `Post`
  is Phase D (packaging). HN stories are mapped onto `BlueskyPost` with a `source` field — a
  deliberate MVP reuse, documented, not a new model.
- **Source seam**: the `Source` protocol covers the *search* step only
  (`search(search_definition, max_posts) -> list[BlueskyPost]`). Bluesky-specific
  post-processing (thread collection, URL expansion, reference expansion) stays orchestrated in
  `CollectStage` and is applied only to Bluesky-sourced posts. Moving that logic inside
  `BlueskySource` is not required and is explicitly out of scope (avoid a large risky refactor).
- **Per-source search params**: MVP keeps `sources:` a plain list of source names; all sources
  share the collection's selected `SearchDefinition`. Per-source parameter customization is
  deferred (note it, don't build it).
- **HN query mapping**: HN Algolia is free-text; MVP joins the search's `include_terms` into
  the query and ignores `exclude_terms` (Algolia has no clean exclusion). Documented deferral.
- **Filename uniqueness**: HN post ids are prefixed (`hn_<objectID>`) so collect filenames
  (`post_hn_<id>.md`) never collide with Bluesky rkeys and the report's `post_<id>.md` lookup
  resolves correctly.
- **`ReportArticle.bluesky_url`**: kept under its legacy name this run (renaming touches
  templates and is Phase D cleanup); for non-Bluesky sources it is populated with the correct
  source permalink. The misnomer is an accepted, documented MVP deviation.
- **Auxiliary output** (render_about/stats/publish) stays out of scope, consistent with Phase B.
- Rejected: a single merged phase — the protocol refactor, the second source, and the report
  badge are each independently shippable and independently verifiable, so they get their own
  commit + check + review cycle. Rejected: renaming `BlueskyPost` / `bluesky_url` now — that is
  Phase D and would inflate the diff without payoff here.
