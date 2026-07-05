# Context — Phase A: Genericize the topic

Source plan: `plans/library_transformation_plan.md`, section **Phase A — Genericize the
topic**. Read that section for intent. This file captures the concrete code the dev
agent needs; do not re-explore unless something below is missing.

## The task in one line
Move the MCP topic definition out of the prompt body and the `is_mcp_related` field name
into configuration + a generic `is_relevant` field, without breaking the existing MCP
pipeline or requiring data migration.

## Files and exactly what's in them

### `config/base/app.yaml`
Current sections: `version`, `metadata`, `paths`, `processing`, `ui`.
- `processing` already has `min_relevance_score: 0.3`, `default_model_config`,
  `default_prompt_config`, etc.
- `ui` has `site_title: "MCP Monitor"`, `site_tagline`, `theme`.
**Add** a new `topic` section, e.g.:
```yaml
topic:
  name: "Model Context Protocol (MCP)"
  description: "MCP is a protocol for AI tool integration that allows language models to access external tools and data sources."
  min_relevance_score: 0.3
```
The `description` text is lifted verbatim from the current prompt body (see prompts.yaml
below) so behavior is unchanged. The `name` is the human phrase the prompt used ("Model
Context Protocol (MCP)").

### `config/base/prompts.yaml`
The `prompts.mcp_evaluation_v1.template` currently begins:
```
Analyze this article for relevance to Model Context Protocol (MCP).

MCP is a protocol for AI tool integration that allows language models to access external tools and data sources.
```
and later instructs:
```
1. is_mcp_related (boolean): Is this article about MCP, AI tool integration, or related topics?
2. relevance_score (0.0-1.0): How relevant is this to MCP? ...
```
Rewrite these to use `{topic_name}` / `{topic_description}` and output `is_relevant`:
- Line 1 → `Analyze this article for relevance to {topic_name}.`
- The MCP definition line → `{topic_description}`
- Item 1 → `is_relevant (boolean): Is this article about {topic_name} or closely related topics?`
- The `relevance_score` wording that says "to MCP" → "to {topic_name}".
- The `key_topics` examples mention "MCP" in the BAD-topics list — leave those examples
  as-is (they are guidance, not topic definition) to keep the diff minimal; renaming them
  is not required. Do NOT introduce a `{` / `}` that isn't a real variable, since the
  template is rendered with `str.format` (see anthropic_client below) — any literal brace
  in the template body would break `.format`. There are currently no literal braces; keep
  it that way.
- Add `topic_name` and `topic_description` to the `variables:` list (required: true).

`config/experiments/experiment_001_sonnet_test.yaml` only overrides `processing`, so it
is unaffected — but confirm it still validates.

### `src/config/config_manager.py`
- Pydantic models mirror the YAML: `PathsConfig`, `ProcessingConfig`, `UIConfig`,
  `MetadataConfig`, then `AppConfig(version, metadata, paths, processing, ui)`.
- **Add** a `TopicConfig(BaseModel)` with `name: str`, `description: str`,
  `min_relevance_score: float = 0.3`, and add `topic: TopicConfig` to `AppConfig`.
- `ConfigManager.load_app_config()` builds `AppConfig(**app_data)`; once YAML has the
  `topic` key it flows through automatically. Experiment-branch merge only touches
  `processing`, so no change needed there.
- Optionally add a `get_topic_config(self) -> TopicConfig` convenience mirroring
  `get_model_config`/`get_prompt_config` — small and consistent with existing style.

### `src/evaluation/anthropic_client.py`
- `AnthropicEvaluator.__init__` already holds `self.config_manager` and loads
  `self.model_config` / `self.prompt_config`. Also load the topic there
  (`self.topic = self.config_manager.load_app_config().topic` or a `get_topic_config()`).
- `_create_evaluation_prompt` (around line 134) renders with
  `template.format(title_part=..., hints_part=..., content=...)`. Add
  `topic_name=self.topic.name, topic_description=self.topic.description` to that
  `.format(...)` call.
- `evaluate_article` (line ~87) builds `ArticleEvaluation(... is_mcp_related=result["is_mcp_related"] ...)`
  → change to `is_relevant=result["is_relevant"]`. The error-path fallback at line ~116
  sets `is_mcp_related=False` → `is_relevant=False`.
- `_parse_response` (line ~162) reads `data.get("is_mcp_related", False)` and returns key
  `"is_mcp_related"` → change both to `is_relevant`. For robustness reading a model that
  still emits the old key, use `data.get("is_relevant", data.get("is_mcp_related", False))`.
  Update the JSONDecodeError default dict (line ~187) key too.

### `src/models/evaluation.py`
- `ArticleEvaluation.is_mcp_related: bool` (line 14) → `is_relevant: bool` with updated
  description. This is the top-of-file field; everything else stays.

### `src/models/url_registry.py`
- `URLEntry.is_mcp_related: bool | None` (line 24) → `is_relevant: bool | None`.

### `src/utils/url_registry.py`
- The DataFrame column list in `__init__` (lines 27-40) includes `"is_mcp_related"` →
  `"is_relevant"`. The backward-compat block (lines 43-54) adds missing columns; also
  handle the case where an old parquet has `is_mcp_related` but not `is_relevant`:
  rename/copy it (e.g. `if "is_mcp_related" in df.columns and "is_relevant" not in df.columns: df["is_relevant"] = df["is_mcp_related"]`).
- `mark_evaluated(self, url, is_mcp_related, relevance_score)` (line 109) — rename the
  param to `is_relevant` and the `self.df.at[idx, "is_mcp_related"]` write (line 120) to
  `"is_relevant"`.
- `get_stats` (lines 124-153): `mcp_related = self.df[self.df["is_mcp_related"] == True]`
  (line 141) → use `"is_relevant"`. The stat dict keys `"mcp_related_urls"` (lines 132,
  149) — rename to `"relevant_urls"` for consistency (see caller note below), or keep;
  prefer renaming to `relevant_urls` and update the empty-dict branch to match.

### `src/evaluation/processor.py`
- Line ~114: `registry.mark_evaluated(url, evaluation.is_mcp_related, evaluation.relevance_score)`
  → `evaluation.is_relevant`.

### `src/stages/evaluate.py`
- Two spots build `evaluation_data` dicts with `"is_mcp_related": evaluation.is_mcp_related`
  (lines ~95 and ~243) → `"is_relevant": evaluation.is_relevant`.
- The human-readable markdown body (lines ~119-126) says "evaluated for MCP relevance"
  and "**MCP Related:** ..." — reword to generic "relevance" / "**Relevant:** ..."
  (cosmetic; keep minimal).
- Stats counter `mcp_related` (lines ~194, 277-278, 316) and `if evaluation.is_mcp_related`
  → rename local to `relevant` and use `evaluation.is_relevant`; update the result dict
  key `"mcp_related"` (line 316) to `"relevant"` (coordinate with CLI print below).

### `src/stages/report.py`
- Two filter spots read stored frontmatter dicts:
  - Line ~149: `if not evaluation.get("is_mcp_related", False): continue`
  - Line ~304: same.
  Change to read the generic field **with old-field fallback** (this is the "read old
  field as fallback when loading existing data" shim from the plan):
  `if not evaluation.get("is_relevant", evaluation.get("is_mcp_related", False)): continue`
- Stat keys `"mcp_related_articles"` (lines ~517, 634) — rename to `"relevant_articles"`
  or leave; if you rename, check nothing downstream reads that exact key (grep first).

### `src/cli/stage_commands.py`
- Line ~250 prints `result['mcp_related']`. If you rename the evaluate result key to
  `"relevant"`, update this to `result['relevant']` and the label text accordingly.

### Tests to update
- `tests/test_models/test_evaluation.py`: constructs `ArticleEvaluation(is_mcp_related=...)`
  and asserts `evaluation.is_mcp_related` / `"is_mcp_related"` in JSON (lines 19, 42, 55,
  84, 103, 113, 128, 143, 158, 174, 194, 200) → rename to `is_relevant`.
- `tests/test_utils/test_url_registry.py`: asserts `"is_mcp_related" in registry.df.columns`
  (line 20), `stats["mcp_related_urls"] == 1` (line 97), `row["is_mcp_related"] is True`
  (line 159) → update to the new column/stat names you chose.

## Decisions / rationale
- **One coherent rename.** Do the field rename everywhere in one pass so no half-renamed
  state ships. The only intentional survivors of `is_mcp_related` are the *fallback reads*
  in `report.py`, `anthropic_client._parse_response`, and `utils/url_registry` compat.
- **Backward compatibility, no migration.** Existing stored markdown/parquet may have the
  old key; fallbacks let reports/registry still read them. New writes use `is_relevant`.
- **Topic description == old prompt text.** Keeping the description verbatim guarantees the
  MCP pipeline's evaluation behavior is unchanged, satisfying the plan's "prove: run the
  existing MCP pipeline unchanged via config only."
- **str.format rendering.** The prompt is rendered with `str.format`; only real variables
  may appear in `{...}`. Keep it that way (no stray literal braces).

## Out of scope (do not do)
- Genericizing `src/templates/*.html` ("MCP Monitor" strings) — deferred.
- Wiring `topic.min_relevance_score` into the report filter plumbing (report uses a literal
  0.3 param default today) — optional at most; do not refactor that flow.
- Collections / multi-config (Phase B), sources (Phase C), packaging (Phase D).

## How to verify (for the check step)
- `uv run poe check` = ruff + ty + pytest. Must pass.
- `uv run nsp validate-config` (or `onsp validate-config`) should still succeed.
- A quick prompt-render assertion (no API): construct an `AnthropicEvaluator` — note its
  `__init__` builds an `Anthropic` client from `settings.anthropic_api_key` but makes no
  network call — and confirm `_create_evaluation_prompt("body")` returns text containing
  the topic name and no unfilled `{topic_` placeholder. If constructing the evaluator is
  awkward, instead assert on the rendered template directly using the loaded prompt +
  topic config. Live Anthropic calls are NOT part of the check (needs ANTHROPIC_API_KEY).
- `grep -rn "is_mcp_related" src/` should return only the documented fallback reads.
