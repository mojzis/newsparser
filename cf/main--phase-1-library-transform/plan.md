# cml plan: phase-1-library-transform

- **Branch**: main
- **Review skill**: python-review
- **Phase count**: 1

## Context
`plans/library_transformation_plan.md` lays out turning newsparser from a single
hardcoded-topic (MCP), single-source (Bluesky) pipeline into a configurable library.
"Phase 1" of that plan is **Phase A — Genericize the topic**: the single biggest
unlock, on which every later phase depends. Today the topic "MCP" is baked into the
Pydantic models (`is_mcp_related`), into filters in `report.py`/`evaluate.py`, and
into the prompt body in `config/base/prompts.yaml`. The template is external but the
topic *definition* lives inside it. This phase moves the topic into configuration and
renames the relevance field to a generic name, while keeping the existing MCP pipeline
behaving identically when run with the default config.

## Final deliverable
The topic ("what is this about") is defined in `config/base/app.yaml` under a new
`topic` section (name + description + min_relevance_score) instead of being hardcoded
in the prompt text. The evaluation prompt template references `{topic_name}` /
`{topic_description}` variables. The relevance field is renamed `is_mcp_related` →
`is_relevant` across models, parsing, stage writes, and filters, with a fallback that
still reads the old field name from previously-stored data. Running the default config
reproduces the current MCP behavior with no data migration. Tests, ruff, and ty stay
green (`uv run poe check`).

## Success criteria
- New `topic` section in `config/base/app.yaml` with `name`, `description`,
  `min_relevance_score`; loaded via a `TopicConfig` model on `AppConfig`.
- `config/base/prompts.yaml` template no longer hardcodes the MCP definition; it uses
  `{topic_name}` and `{topic_description}`, and asks the model to output `is_relevant`.
- `AnthropicEvaluator` injects the topic values when rendering the prompt and parses
  `is_relevant` from the response.
- `ArticleEvaluation` and `URLEntry` expose `is_relevant` (not `is_mcp_related`);
  reading old stored data (frontmatter / parquet) with the old key still works.
- `report.py` and `evaluate.py` filter on the generic field with old-field fallback.
- No stray `is_mcp_related` references remain except the documented backward-compat
  fallbacks. `uv run poe check` passes; existing tests updated to the new field name.

## Phase 1: Genericize the topic (Phase A)
**Deliverable**: Topic defined in config, prompt parameterized, relevance field renamed
to `is_relevant` with backward-compat reads, MCP pipeline unchanged via default config.
**Steps**: dev, check, review

## Notes
- This is intentionally MVP-sized per the repo's CLAUDE.md and the plan's "each phase
  independently shippable, MVP-sized" framing. Templates (`src/templates/*.html`) still
  hardcode "MCP Monitor"; genericizing those HTML strings is **out of scope** for this
  phase (the plan defers site chrome; the proof here is "run the MCP pipeline unchanged").
- `min_relevance_score` already exists under `processing` in config but is not actually
  wired into `report.py` (the filter uses a literal `0.3` default param). Adding it to
  `topic` is for future collections; wiring it through is optional and low priority —
  do not expand scope to refactor the report filter plumbing.
- Live end-to-end proof calls the Anthropic API and needs `ANTHROPIC_API_KEY`; that is
  not part of the automated check. The check step verifies via the test suite plus a
  prompt-render assertion and config validation instead.
