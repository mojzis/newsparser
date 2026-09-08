# Phase 1 — check

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need.

## Verifies
A minimal `Source` abstraction exists, `BlueskyPost` carries a `source` field defaulting to
`"bluesky"`, collect-stage frontmatter records it, and the `mcp` pipeline behaves identically
(no behavior change beyond the additive field).

## Verification steps
1. `uv run poe check` — ruff + ty green, pytest green with no fewer than the 355 baseline tests
   (new tests should raise the count). Paste the tail.
2. Confirm `BlueskyPost` has `source: str` defaulting to `"bluesky"`, and that constructing a
   `BlueskyPost` from a dict lacking `source` yields `source == "bluesky"` (backward compat).
3. Confirm `src/sources/base.py` defines the `Source` protocol/ABC (`name` + async `search`) and
   `src/sources/bluesky.py` defines `BlueskySource` implementing it; verify `CollectStage`'s search
   path now goes through `BlueskySource` (grep that the direct `get_posts_by_definition` call in
   `collect_posts` is replaced, and that thread/URL/reference expansion is untouched).
4. Confirm `CollectStage.post_to_markdown` frontmatter includes `"source"`; if practical, build a
   `BlueskyPost` and call `post_to_markdown` in a scratch snippet and confirm `source: bluesky` is
   present.
5. Confirm the `mcp` pipeline is otherwise unchanged: no edits to templates, report stage, evaluate
   stage, or collection config; `git show --stat HEAD` (and any sibling phase-1 commits) touch only
   the in-scope files (plus cf/ orchestration docs).

## Pass condition
`poe check` green; `source` field present with `"bluesky"` default and backward-compat read;
`BlueskySource`/`Source` present and used by collect; frontmatter records `source`; no
out-of-scope behavior change.

## Constraints
- Read-only. Do NOT modify code or commit. If the deliverable is broken, report it — do not fix it.

## Report
Return ONLY this JSON:
{"verified": true, "evidence": "what you observed (paste output)", "deviations": ["..."], "issues": ["..."]}

## Deviations from earlier steps
- phase 1 dev: Wired BlueskySource with an optional injected client (defaulting to owning its own when none given) so CollectStage reuses one authenticated Bluesky session instead of logging in twice per collect run; flagged by python-review as a should-fix and addressed within scope.

## Additional verification (post-review fixes)
Verify each of these findings was addressed:
- Misleading test `test_search_returns_bluesky_stamped_posts` in tests/test_sources/test_bluesky.py no longer asserts a no-op source-stamping behavior; either renamed to reflect actual delegation/context behavior or the trivial source assertion was dropped.
