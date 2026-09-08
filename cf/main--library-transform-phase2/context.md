# Shared context — Phase B (Collections)

This is the required-reading brief the planner assembled by exploring the repo. Do NOT
re-explore these files unless something here is missing what you need.

## What Phase A already did (predecessor run)
Genericized the MCP topic into config and renamed the relevance field. Relevant facts:
- `src/config/config_manager.py` defines Pydantic models:
  - `TopicConfig(BaseModel)`: `name: str`, `description: str`, `min_relevance_score: float = 0.3`
  - `UIConfig(BaseModel)`: `site_title: str = "MCP Monitor"`, `site_tagline: str = "..."`, `theme: str = "default"`
  - `PathsConfig`, `ProcessingConfig`, `MetadataConfig`, `AppConfig` (has `topic: TopicConfig`, `ui: UIConfig`, `processing`, `paths`), `ModelConfig`, `PromptConfig`, etc.
  - `ConfigManager` is a **global singleton** via `get_config_manager()` driven by env vars
    `NSP_CONFIG_PATH` (default `config`) and `NSP_CONFIG_BRANCH` (default `base`). Methods:
    `get_model_config(id=None)`, `get_prompt_config(id=None)`, `get_topic_config()`,
    `load_app_config()`, `validate_config()`.
- `config/base/app.yaml` holds the current `topic:` (name "Model Context Protocol (MCP)",
  description "MCP is a protocol for AI tool integration…", min_relevance_score 0.3) and
  `ui:` (site_title "MCP Monitor", site_tagline "Daily digest of Model Context Protocol
  mentions", theme "default"), and `processing.default_model_config: "mcp_evaluator_v1"`,
  `processing.default_prompt_config: "mcp_evaluation_v1"`.
- Prompt template in `config/base/prompts.yaml` uses `{topic_name}`/`{topic_description}`.
- The relevance field is `is_relevant` on `ArticleEvaluation` and `URLEntry`; read paths
  fall back to the old `is_mcp_related` for legacy data. `src/stages/report.py` has a
  module-level `_is_relevant(evaluation: dict)` helper for this. Leave that alone.
- Phase A deviation still open: `topic.min_relevance_score` is **never read** (report.py
  hardcodes 0.3). Do NOT wire it in this run — out of scope.

## Key models / files you will touch or reuse

### Search config — `src/config/searches.py`
- `SearchDefinition(BaseModel)`: `name`, `description`, `include_terms: list[str]`,
  `exclude_terms: list[str] = []`, `sort="latest"`, `enabled=True`, `query_syntax="native"`.
- `SearchConfig(BaseModel)`: `searches: dict[str, SearchDefinition]`; methods
  `get_search(key)`, `get_enabled_searches()`, `load_from_file(path)`,
  `model_validate(data)`. Validator requires ≥1 enabled search.
- `load_search_config(config_path=None)` currently loads `src/config/searches.yaml`
  (a copy of `config/base/searches.yaml`) or falls back to hardcoded defaults.
- Base searches keys: `mcp_mentions`, `mcp_tools`, `mcp_tag`, `mcp_integrations`.
- CLI `--search` default is `"mcp_tag"`.

### Stages — all already accept a `base_path` constructor arg (default `Path("stages")`)
- `src/stages/base.py`: `Stage.__init__(stage_name, base_path=Path("stages"))` →
  `self.base_path`, `self.stage_path = base_path/stage_name`, dirs are
  `base_path/stage_name/YYYY-MM-DD`. `ProcessingStage.__init__(stage_name,
  input_stage_name, base_path)` sets `self.input_stage_path = base_path/input_stage_name`.
- `src/stages/collect.py`: `CollectStage(settings, search_definition, max_posts, expand_urls,
  collect_threads, max_thread_depth, max_parent_height, export_parquet, expand_references,
  max_reference_depth, base_path=Path("stages"))`, calls `super().__init__("collect", base_path)`.
- `src/stages/fetch.py`: `FetchStage(base_path=Path("stages"), export_parquet=True)` →
  `super().__init__("fetch", "collect", base_path)`. Uses `self.base_path/self.stage_name`.
- `src/stages/evaluate.py`: `EvaluateStage(settings, base_path=Path("stages"),
  export_parquet=True)` → `super().__init__("evaluate", "fetch", base_path)`. Constructs
  `self.evaluator = AnthropicEvaluator(settings)` in `__init__`. Uses `self.base_path/...`.
- `src/stages/report.py`: `ReportStage(template_dir=None, base_path=Path("stages"))` →
  `super().__init__("report", "evaluate", base_path)`.
  **Hardcoded paths inside report.py that break namespacing** (must become collection-aware
  in Phase 2 — use `self.base_path/…` and a per-collection output dir):
  - line ~70:  `fetch_dir = Path("stages/fetch") / …`
  - line ~199: `"stages/collect"` (string)
  - line ~342: `collect_dir = Path("stages/collect") / …`
  - line ~445: `reports_dir = Path("output") / "reports" / …`
  It builds a `ReportGenerator` (see below) for actual HTML writing.

### Report generator — `src/reports/generator.py`
- `ReportGenerator(template_dir=None, output_dir=None)` — `output_dir` defaults to
  `Path("output")`; writes daily reports to `output_dir/"reports"/YYYY-MM-DD/report.html`
  and the homepage. It renders Jinja templates but **does not currently pass any
  site_title/tagline into the render context** (templates hardcode the strings).
- `generate_daily_report(report_day)` renders `daily.html` with `date_formatted`,
  `articles`, `active_menu`. `generate_homepage(homepage_data)` renders `homepage.html`.

### Evaluator — `src/evaluation/anthropic_client.py`
- `AnthropicEvaluator.__init__(self, settings)`: sets `self.config_manager =
  get_config_manager()`, then `self.model_config = get_model_config()`,
  `self.prompt_config = get_prompt_config()`, `self.topic = get_topic_config()`.
  `_create_evaluation_prompt` formats the template with
  `topic_name=self.topic.name, topic_description=self.topic.description`.
  To make it collection-aware: accept the collection (or explicit topic + prompt_id +
  model_id) and resolve `get_prompt_config(id)` / `get_model_config(id)` by the
  collection's selection; keep the no-collection path as today's default.

### Templates — `src/templates/` (Jinja2, autoescape on for html/xml)
Hardcoded site branding to templatize in Phase 3:
- `base.html:6` `<title>{% block title %}MCP Monitor{% endblock %}</title>`
- `base.html:268` `<a href="/index.html">Bluesky MCP Monitor</a>`
- `homepage.html:3` `<div class="header">MCP Monitor</div>` and `:4` tagline block
- `about.html:3` `About - MCP Monitor`
- `daily.html:2` `MCP Monitor - {{ date_formatted }}`, `:5` `MCP Monitor</a> - …`
Approach: render context gains `site_title` / `site_tagline`; templates use
`{{ site_title | default('MCP Monitor') }}` etc. Keep `theme` out of scope.

### CLI — two entry points, both call into `src/cli/stage_commands.py`
- `nsp` → `src/cli/new_commands.py` (top-level convenience commands `collect`, `fetch`,
  `evaluate`, `report`, `run_all`, `status`, `present`, `publish`) that build a
  `click.Context` and `ctx.invoke(...)` the matching command in `stage_commands.py`.
- `nsp stages …` and `onsp …` legacy.
- `src/cli/stage_commands.py` holds the real command bodies: `collect`, `fetch`,
  `evaluate`, `report`, `run_all`, `status`, `list_files`, `clean`, `publish`,
  `render_stats`, `render_about`, `present`. These construct the stage objects with the
  **default** `Path("stages")` today. `status`/`list_files`/`clean` hardcode
  `Path("stages")` for their directory scans.
- `collect` loads searches via `load_search_config(config_path)` then
  `search_config.get_search(search)`.
- `new_commands.cli()` group runs `get_config_manager().validate_config()` on startup.

## Environment / tooling
- Run everything with `uv run …`. Tests: `uv run poe check` = ruff check + `ty check src/`
  (both must pass) + full `pytest -q`. Current baseline: ~336 tests pass, ruff & ty clean.
- **There are no git pre-commit hooks configured.** So you MUST run `uv run poe check`
  yourself before committing — nothing else will enforce it.
- Tests live under `tests/test_config/`, `tests/test_reports/`, etc. Add collection tests
  in `tests/test_config/test_collection.py`.
- `stages/`, `output/`, `reports/`, `data/` are gitignored and absent locally — no data to
  migrate, no orphaning concern.
- MVP rules (project CLAUDE.md): minimal implementation, no speculative abstractions, keep
  it simple. Neutral commit/report tone; commit footer `🤖 Generated with
  [Claude Code](https://claude.ai/code)`; use `git add -A`.

## Design agreed for this run (do not redesign)

### CollectionConfig (Phase 1) — new `src/config/collection.py`
Reuse existing models; do not duplicate them.
```
from src.config.config_manager import TopicConfig, UIConfig
from src.config.searches import SearchConfig

class EvaluationSelection(BaseModel):
    prompt_config: str
    model_config_name: str   # NOTE: avoid the name `model_config` — Pydantic reserves it.
                             # Use e.g. `model_config_name` (or alias) mapping YAML key `model_config`.

class CollectionConfig(BaseModel):
    name: str
    topic: TopicConfig
    ui: UIConfig
    evaluation: EvaluationSelection
    searches: SearchConfig
    default_search: str

    @property
    def stages_base(self) -> Path: return Path("stages") / self.name
    @property
    def output_base(self) -> Path: return Path("output") / self.name
```
- `load_collection(name: str, config_dir: str | Path = "config") -> CollectionConfig`
  reads `config_dir/collections/<name>.yaml`, raises `FileNotFoundError` for unknown names.
- **Pydantic gotcha**: a field literally named `model_config` collides with Pydantic's
  reserved `model_config` class attribute. Name the Python field differently and map the
  YAML `model_config:` key via a Field alias, or just name the YAML key `evaluator` /
  `model` — pick one and keep it consistent across both YAMLs and the evaluator wiring.
  Validate the YAMLs actually load (a quick `uv run python -c "from src.config.collection
  import load_collection; print(load_collection('mcp'))"`).
- `default_search` must name a key present (and enabled) in that collection's `searches`.

### Collection YAMLs (Phase 1)
- `config/collections/mcp.yaml`: `name: mcp`; `topic:` copied verbatim from
  `config/base/app.yaml` topic; `ui:` copied from app.yaml ui; `evaluation:` →
  prompt_config `mcp_evaluation_v1`, model `mcp_evaluator_v1`; `searches:` = the full
  contents of `config/base/searches.yaml` (embed inline); `default_search: mcp_tag`.
  This collection must reproduce today's behavior exactly.
- `config/collections/duckdb.yaml`: `name: duckdb`; a real DuckDB topic (e.g. name
  "DuckDB", description a one-paragraph "in-process analytical SQL database…",
  min_relevance_score 0.3); `ui:` site_title "DuckDB News", tagline "Daily digest of
  DuckDB mentions"; `evaluation:` reuse the same `mcp_evaluation_v1` prompt +
  `mcp_evaluator_v1` model (the prompt is now generic via topic vars — fine to reuse);
  `searches:` one or two searches (e.g. `duckdb_mentions` with include_terms ["duckdb",
  "duck db"], enabled true); `default_search: duckdb_mentions`.

### Wiring (Phase 2)
- Add `--collection` (default `"mcp"`) to `collect`, `fetch`, `evaluate`, `report`,
  `run_all`, `status`, `list_files`, `clean` in `stage_commands.py`, and mirror it on the
  matching `new_commands.py` convenience wrappers (pass through `ctx.invoke`).
- In each command, `collection = load_collection(name)` and pass
  `base_path=collection.stages_base` to the stage constructors. `collect` should use
  `collection.searches.get_search(search or collection.default_search)` instead of
  `load_search_config`. `status`/`list_files`/`clean` scan `collection.stages_base`.
- `EvaluateStage` gains a `collection` param and passes it to `AnthropicEvaluator`.
- `ReportStage` gains an `output_base` (or `collection`) so its `Path("output")` and the
  internal `Path("stages/fetch")` / `Path("stages/collect")` references use
  `self.base_path/…` and the collection output dir; it builds `ReportGenerator(
  output_dir=collection.output_base)`.
- Keep the no-`--collection` default = `mcp`, so existing invocations still work.

### UI (Phase 3)
- Thread `site_title`/`site_tagline` from `collection.ui` into `ReportGenerator` (store on
  the instance, add to every `template.render(...)` context) and templatize the hardcoded
  strings listed above with `{{ site_title | default('MCP Monitor') }}` /
  `{{ site_tagline | default('…') }}`.
