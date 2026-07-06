# Phase 2 — check

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need.

## Verifies
A `HackerNewsSource` maps Algolia stories to the post model with `source="hackernews"`;
`CollectionConfig` has a `sources` list (default `["bluesky"]`); `CollectStage` dispatches over
the configured sources with Bluesky-only expansion isolation and Bluesky-credential gating; the
`mcp` collection stays Bluesky-only and unchanged while `duckdb` lists `[bluesky, hackernews]`.

## Verification steps
1. `uv run poe check` — ruff + ty green, pytest green (count ≥ Phase 1's). Paste the tail.
2. `HackerNewsSource`: using a mocked/sample Algolia payload (an offline snippet with a
   representative `hits` list, or the unit tests), confirm each hit maps to a `BlueskyPost` with
   `source="hackernews"`, `id` prefixed `hn_`, `content` = title, engagement from
   points/num_comments, `links` populated only when `url` is set, and empty-title hits skipped.
   Confirm no real network call happens in the test suite.
3. `CollectionConfig`: confirm `sources` defaults to `["bluesky"]`; `duckdb.yaml` loads with
   `sources == ["bluesky", "hackernews"]`; `mcp.yaml` resolves to Bluesky-only. If a validator was
   added, confirm an unknown source name raises. Confirm `test_mcp_matches_base_app_config` still
   passes.
4. `CollectStage` dispatch: verify it builds sources from the collection and aggregates posts;
   confirm Bluesky-only expansion (threads/URL/reference) is guarded to Bluesky posts (read the
   code / run a unit test with a fake multi-source setup). Confirm HN posts are written with correct
   filenames (`post_hn_<id>.md`) — no collision with Bluesky.
5. Credential gating: confirm collecting a Bluesky-less collection does not exit on missing Bluesky
   credentials, and a Bluesky-including collection still requires them.
6. `git show --stat` across phase-2 commits touches only in-scope files (+ cf/ docs).

## Pass condition
`poe check` green; HN mapping correct and offline; `sources` config works with safe defaults and
mcp parity intact; collect dispatches across sources with Bluesky-only expansion and correct
credential gating.

## Constraints
- Read-only. Do NOT modify code or commit. If the deliverable is broken, report it — do not fix it.
- Do NOT make real network calls to Hacker News; rely on tests/mocks and code inspection.

## Report
Return ONLY this JSON:
{"verified": true, "evidence": "what you observed (paste output)", "deviations": ["..."], "issues": ["..."]}

## Deviations from earlier steps
- phase 1 dev: Wired BlueskySource with an optional injected client (defaulting to owning its own when none given) so CollectStage reuses one authenticated Bluesky session instead of logging in twice per collect run; flagged by python-review as a should-fix and addressed within scope.

## Deviations from earlier steps
- phase 1 check: Confirmed the phase 1 dev deviation (BlueskySource optional injected client) is in-scope and correctly wired; no code changes made by check.

## Deviations from earlier steps
- phase 2 dev: Factored a shared src/sources/registry.py (SOURCE_FACTORIES/KNOWN_SOURCES) used by both CollectStage._build_sources and CollectionConfig source validator, to avoid duplicating the known-source set; added after python-review flagged duplication as a should-fix, within the brief in-scope files.

## Additional verification (post-review fixes)
Verify each of these findings was addressed:
- `test_hackernews_only_skips_bluesky_client` in tests/test_stages/test_collect_stage.py renamed to `test_hackernews_only_skips_bluesky_source` (or equivalent), so its name no longer implies the BlueskyClient object itself is conditionally constructed.
