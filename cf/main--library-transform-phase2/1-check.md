# Phase 1 — check

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need.

## Verifies
The Collection config data layer exists and resolves correctly: `CollectionConfig` +
`load_collection` in `src/config/collection.py`, plus `mcp.yaml` (reproducing today's
config) and `duckdb.yaml` (a distinct topic), with passing tests — and no change to the
running pipeline yet.

## Verification steps
1. `uv run poe check` — confirm ruff clean, ty clean, and the full pytest suite passes
   (baseline was ~336; the new collection tests should add to that). Paste the tail.
2. Confirm `config/collections/mcp.yaml` and `config/collections/duckdb.yaml` exist and
   that both load:
   `uv run python -c "from src.config.collection import load_collection; m=load_collection('mcp'); d=load_collection('duckdb'); print(m.name, m.stages_base, m.output_base); print(m.topic.name); print(d.name, d.topic.name, d.ui.site_title, d.default_search)"`.
3. Assert `mcp` reproduces today's config: its `topic.name`/`description`/
   `min_relevance_score` equal the `topic:` block in `config/base/app.yaml`, and its
   `searches` include `mcp_tag` (its `default_search`). Its `stages_base` is
   `stages/mcp`, `output_base` is `output/mcp`.
4. Confirm `duckdb` resolves a genuinely different topic + ui (not "MCP"/"MCP Monitor")
   and that `searches.get_search(default_search)` is enabled.
5. Confirm `load_collection('nonexistent')` raises.
6. Confirm nothing outside the in-scope files changed: `git show --stat HEAD` should touch
   only `src/config/collection.py`, the two collection YAMLs, and the new test file (plus
   any lockfile only if a dep was added — none should be needed).

## Pass condition
`poe check` green; both collections load; `mcp` matches app.yaml topic and namespaced
paths; `duckdb` is a distinct topic/ui; unknown-name raises; no out-of-scope files touched.

## Constraints
- Read-only. Do NOT modify code or commit. If the deliverable is broken, report it — do not fix it.

## Report
Return ONLY this JSON:
{"verified": true, "evidence": "what you observed (paste output)", "deviations": ["..."], "issues": ["..."]}
