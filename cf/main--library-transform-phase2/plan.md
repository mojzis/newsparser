# cml plan: library-transform-phase2 (Collections / Phase B)

- **Branch**: main
- **Review skill**: python-review
- **Phase count**: 3

## Context
This is Phase B ("Collections / profiles") of `plans/library_transformation_plan.md`.
Phase A (the run logged under `cf/main--phase-1-library-transform/`) is complete: the
MCP topic is now a config section (`TopicConfig` in `src/config/config_manager.py`,
`topic:` block in `config/base/app.yaml`), the prompt template takes
`{topic_name}`/`{topic_description}`, and `is_mcp_related` was renamed to `is_relevant`
with backward-compat fallback reads. See `context.md` for the Phase A deviations that
matter here.

Phase A left one loose thread relevant to us: `topic.min_relevance_score` is defined in
config but never read (report.py still hardcodes a 0.3 default). We do **not** need to
wire it in — it stays out of scope unless trivially free.

The vision this phase unlocks: run N themed news collections side by side. A collection
is one YAML bundle (topic + searches + prompt/model selection + ui) whose data and
output are namespaced by collection name, so two topics never collide on disk.

Constraints: MVP methodology (see project CLAUDE.md) — minimal implementation, no extra
abstractions, working over perfect. `stages/`, `output/`, `reports/`, `data/` are all
gitignored and there is **no local data** right now, so namespacing paths under a
collection name orphans nothing and needs no migration.

## Final deliverable
A `Collection` config abstraction and a `--collection <name>` flag threaded through the
CLI so the whole collect → fetch → evaluate → report pipeline runs per collection with
data under `stages/<name>/…` and output under `output/<name>/…`. The default collection
`mcp` reproduces today's behavior; a second collection `duckdb` on a genuinely different
topic proves the abstraction — its pipeline routes to its own directories and its
generated site is branded from its own `ui`/`topic` config rather than hardcoded "MCP".

## Success criteria
- `config/collections/mcp.yaml` and `config/collections/duckdb.yaml` load and validate.
- The `mcp` collection resolves to the exact topic/searches/prompt used today.
- `nsp <stage> --collection duckdb` (and `run-all`, `status`, `list-files`, `clean`)
  read/write only under `stages/duckdb/…` and `output/duckdb/…`.
- The evaluator uses the collection's topic + prompt/model, not the global default.
- Generated report/homepage for `duckdb` shows the duckdb site title/tagline, not "MCP".
- `uv run poe check` stays green (ruff + ty + full pytest suite, ~336 tests) throughout.

## Phase 1: Collection config abstraction
**Deliverable**: A new `src/config/collection.py` with a `CollectionConfig` Pydantic model
(reusing `TopicConfig`, `UIConfig`, `SearchConfig`) and a `load_collection(name)` loader,
plus derived `stages_base`/`output_base` path properties; two collection YAMLs
(`config/collections/mcp.yaml` reproducing current config, `config/collections/duckdb.yaml`
for a second topic); and unit tests. No pipeline wiring yet — this is the pure data layer.
**Steps**: dev, check, review

## Phase 2: Wire collections through CLI and stages
**Deliverable**: `--collection` option (default `mcp`) on all stage commands; stages
instantiated with the collection's namespaced `base_path`; report/collector read the
collection's searches, topic, prompt/model; report.py internal hardcoded stage paths and
`output` path made collection-aware; evaluator threaded with the collection. Running the
`duckdb` collection routes all reads/writes to its own directories.
**Steps**: dev, check, review

## Phase 3: Per-collection site branding (ui)
**Deliverable**: `site_title`/`site_tagline` from the collection's `ui` flow into the
report/homepage/daily render contexts; the hardcoded "MCP Monitor" / "Bluesky MCP Monitor"
strings in the Jinja templates become `{{ site_title }}` (with a sensible default). Proof:
the `duckdb` collection generates a correctly-branded, separate site.
**Steps**: dev, check, review

## Notes
- Decision: **uniform namespacing** — even the default `mcp` collection writes to
  `stages/mcp/…` and `output/mcp/…` (the plan mandates `stages/<collection>/collect/…`).
  Safe because those dirs are gitignored and empty locally. Deployment/R2 path changes are
  Phase E's concern, deliberately out of scope here.
- Decision: auxiliary output (`render_stats`, `render_about`, `publish`, `present`,
  DuckDB query page) stays at `output/` root as shared site chrome — **not** namespaced
  per collection in this run. Namespacing the four core stages + report output is enough to
  prove collections. Broader namespacing is deferred (note it, don't build it).
- Decision: collections embed their `searches` inline (self-contained "one YAML bundle")
  and select `prompt_config`/`model_config` by id from the existing `config/base` configs;
  a `default_search` key names which embedded search `--search` uses when unspecified.
- `topic.min_relevance_score` remains unwired (Phase A left it dead); do not wire it.
- Rejected: separate config-resolution vs path-namespacing phases — a Collection resolves
  both config and paths, so they belong together in the model (Phase 1) and are consumed
  together (Phase 2).
