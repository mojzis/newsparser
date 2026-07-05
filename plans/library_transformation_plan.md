# Library Transformation Plan — Themed News Collections

Goal (from TODO_later.md and configuration_externalization_plan.md Phase 4):
turn newsparser into a library that lets anyone define a topic + searches and get
a daily themed news website — multiple sources, custom prompts, swappable styling.

## Where we are

Working end-to-end pipeline for one hardcoded topic (MCP) and one source (Bluesky):

- Stage-based architecture (`src/stages/`): collect → fetch → evaluate → report,
  fault-tolerant per-item markdown files. Solid foundation, keep as-is.
- Config externalization largely done: `config/base/{app,models,prompts,searches}.yaml`,
  `ConfigManager`, prompt/model versioning stamped into evaluation records,
  experiments dir. The old config plan's Phases 1–2 are essentially complete.
- Clean codebase: tests green (~336), ruff clean, Pydantic v2, typer CLI (`nsp`/`onsp`).

## What blocks the vision

1. **Topic is hardcoded**, not configured: `is_mcp_related` in models
   (`src/models/evaluation.py`, `url_registry.py`), MCP filtering in
   `src/stages/report.py` and `evaluate.py`, MCP baked into the prompt text.
   The prompt *template* is external, but the topic definition lives inside it.
2. **Single source**: only Bluesky; no source abstraction
   (TODO_more_sources.md wants HN, Reddit, GitHub, Lobste.rs, RSS, podcasts).
3. **One config = one site**: no concept of running N collections side by side.
4. **Not packaged as a library**: package is `src.*`, no public API,
   templates not overridable.
5. **No deployment**: `.github/workflows/` is empty despite the GitHub Actions plan.

## Phases (each independently shippable, MVP-sized)

### Phase A — Genericize the topic
The single biggest unlock; everything else depends on it.

- Add a `topic` section to app/profile config: `name`, `description`
  (the "what is this about" paragraph currently hardcoded in the prompt),
  `min_relevance_score`.
- Prompt template gets `{topic_name}` / `{topic_description}` variables;
  MCP text moves from `prompts.yaml` template body into topic config.
- Rename `is_mcp_related` → `is_relevant` in models and stages;
  read old field as fallback when loading existing data (one-line shim, no migration).
- `report.py` / `evaluate.py` filter on the generic field; site title/tagline
  already come from `app.yaml`.
- Prove: run the existing MCP pipeline unchanged via config only.

### Phase B — Collections (profiles)
- A collection = one YAML bundle: topic + searches + prompt selection + ui + paths.
  Directory: `config/collections/<name>.yaml` (base configs stay as defaults).
- CLI: `nsp run-all --collection mcp` (default = current behavior);
  stages/output/report paths namespaced per collection
  (`stages/<collection>/collect/...`, `reports/<collection>/...`).
- Prove: create a second collection on a genuinely different topic
  (e.g. "duckdb" or "local-first") and generate its site.

### Phase C — Source abstraction + second source
- Extract a minimal `Source` protocol from the Bluesky collector:
  `search(query, since) -> list[Post]`. Add `source: str` field to the post model.
- Collection config lists sources with per-source search params.
- First new source: **Hacker News via Algolia API** — free, no auth, JSON,
  trivially searchable (TODO_more_sources.md's own recommendation).
  RSS (Lobste.rs & generic feeds) is the natural third, also cheap.
- Report shows source badge per item; no per-source report sections yet.

### Phase D — Package as a library
Do this only after B/C stabilize the shapes.

- Rename `src` → real package name (e.g. `newsparser`), fix entry points.
- Public API surface: roughly `Collection.load(path)` + `run(stage, date)`;
  CLI becomes a thin wrapper.
- Templates: config key for a user template dir that overrides built-ins
  (Jinja2 `ChoiceLoader` — a few lines).
- `examples/` dir with two collection configs; short README for
  "build your own themed site".

### Phase E — Automation & publishing
- GitHub Actions daily workflow: matrix over collections, secrets from repo,
  run-all + upload (R2 as now; GitHub Pages as the zero-cost alternative for
  library users).
- Failure notification via GitHub issue (already in the original spec).

## Deliberately deferred (backlog, don't block the library)

- Reddit/GitHub/podcast sources; YouTube API; paywall detection
- A/B testing framework (config plan Phase 3) — prompt versioning already
  stamped in data, which is the part that matters
- Anthropic cost tracking; quality metrics; authors overview;
  duckdb-js search page; content-type/key-topics prompt tuning

## Order rationale

A before B: a collection is only meaningful once topic is config.
C after B: sources plug into a collection, and HN proves the abstraction.
D after C: freezing a public API before the source protocol exists would
mean re-breaking it. E last: automation only pays once multi-collection works.
