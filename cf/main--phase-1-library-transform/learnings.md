# Learnings: phase-1-library-transform

## What worked
- Single phase covering both config genericization (TopicConfig) and the is_mcp_related → is_relevant rename went cleanly through dev/check in one pass.
- Backward-compat fallback reads (dict and pandas column) kept old stage data working without a migration step, matching MVP principles.
- python-review caught a real accidental leftover (hardcoded "MCP" in the relevance_score prompt line) that automated tests couldn't detect since it's plain text, not template syntax.

## Friction
- One fix round was needed: review found a leftover hardcoded topic reference and a misleading code comment. Both were minor, low-risk fixes.
- dev agent proactively applied a few review-driven cleanups (dedup fallback into `_is_relevant()` helper) ahead of the review step, which reduced review findings but slightly blurred the line between "brief scope" and "review scope."

## Suggestions for cml/SKILL.md
- No process changes suggested — single fix round resolved all findings, checks were unambiguous (verified: true both times).
