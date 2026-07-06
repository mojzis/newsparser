# Phase 3 — dev

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need.

## Task
Surface a per-item source badge in the daily report and make the "via" permalink source-aware.

1. `src/models/report.py`: add `source: str = "bluesky"` to `ReportArticle`. Add a `source` param
   to `from_post_and_evaluation` and build the permalink source-appropriately:
   - `bluesky`: keep `https://bsky.app/profile/{author}/post/{actual_post_id}` (unchanged).
   - `hackernews`: `https://news.ycombinator.com/item?id=<objectID>` where `<objectID>` is the
     post id with the `hn_` prefix stripped.
   Keep the field name `bluesky_url` (renaming is Phase D) — it now holds the source permalink.
   Consider a small helper/property for a human label (`"Bluesky"`, `"Hacker News"`, else the raw
   source) for the template, or expose the raw `source` and map it in the template — your call, keep
   it minimal.
2. `src/stages/report.py`: in **both** post-lookup blocks (~lines 158-284 and ~315-425), read
   `source = post_md.get_frontmatter_value("source", "bluesky")` alongside `author`/`created_at`,
   default `"bluesky"` when the post isn't found, and pass it into `from_post_and_evaluation`.
3. `src/templates/daily.html`: add a source badge to the article meta line (line ~16, the
   `•`-separated `via ... at ... • domain` line) — e.g. `• {{ article.source_label }}`, styled
   consistently with the existing meta. If `homepage.html` renders per-article meta, add the badge
   there too; if it doesn't list per-article source info, leave it.
4. Tests: assert `ReportArticle` carries `source`, that HN articles get the HN permalink, and that
   the rendered daily report contains the badge (extend existing report/generator tests).

## In-scope files
- `src/models/report.py`
- `src/stages/report.py`
- `src/templates/daily.html` (and `homepage.html` only if it shows per-article meta)
- `tests/` (report model + render tests)

## Out of scope
- Renaming `bluesky_url` or `BlueskyPost` (Phase D).
- Per-source report sections / grouping (plan says "no per-source sections yet").
- `render_about` / stats / publish auxiliary output.
- Changing collect/fetch/evaluate stages — `source` is already in collect frontmatter from Phase 1.

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

## Deviations from earlier steps
- phase 1 dev: Wired BlueskySource with an optional injected client (defaulting to owning its own when none given) so CollectStage reuses one authenticated Bluesky session instead of logging in twice per collect run; flagged by python-review as a should-fix and addressed within scope.

## Deviations from earlier steps
- phase 1 check: Confirmed the phase 1 dev deviation (BlueskySource optional injected client) is in-scope and correctly wired; no code changes made by check.
