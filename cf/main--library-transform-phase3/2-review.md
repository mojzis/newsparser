# Phase 2 — review

See [context.md](./context.md) — required reading. The planner already explored what's in there; do NOT re-explore unless context.md is missing something you need.

## Review skill
python-review

## Commit range
<base sha for this phase — provided by orchestrator; overall plan base is fd7c507>..HEAD

## Task
1. Invoke the review skill (use the `Skill` tool) over the commit range.
2. For each finding, decide if it's real and actionable. Drop false positives and pre-existing
   issues. Keep MVP scope in mind: ignoring HN `exclude_terms`, sources sharing one
   `SearchDefinition` (no per-source params), reusing `BlueskyPost` for HN, and the plain-list
   `sources` shape are all deliberate documented decisions — not defects. Do scrutinize: the HN→post
   mapping (null url, missing fields, empty titles, timezone of `created_at`), error handling on the
   HTTP call, the multi-source dispatch and Bluesky-only expansion isolation, filename uniqueness,
   and the relaxed credential gating.
3. Report only. Do NOT fix anything, do NOT commit.

## Report
Return ONLY this JSON:
{"findings": [{"description": "...", "file": "...", "severity": "high|medium|low"}], "dropped": ["finding + why not actionable"], "deviations": ["..."]}

## Deviations from earlier steps
- phase 1 dev: Wired BlueskySource with an optional injected client (defaulting to owning its own when none given) so CollectStage reuses one authenticated Bluesky session instead of logging in twice per collect run; flagged by python-review as a should-fix and addressed within scope.

## Deviations from earlier steps
- phase 1 check: Confirmed the phase 1 dev deviation (BlueskySource optional injected client) is in-scope and correctly wired; no code changes made by check.

## Deviations from earlier steps
- phase 2 dev: Factored a shared src/sources/registry.py (SOURCE_FACTORIES/KNOWN_SOURCES) used by both CollectStage._build_sources and CollectionConfig source validator, to avoid duplicating the known-source set; added after python-review flagged duplication as a should-fix, within the brief in-scope files.
