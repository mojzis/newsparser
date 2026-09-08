# Phase 3 — fix

See [context.md](./context.md) — required reading.

## Task
Fix the review findings below. Fix only these — no drive-by changes.

## Findings
[{"description": "Homepage tagline silently changes for the existing mcp collection. The old homepage.html hardcoded 'Daily digest of Model Context Protocol discussions from Bluesky'; the templatized version now renders collection.ui.site_tagline, which for config/collections/mcp.yaml (and the UIConfig/ReportGenerator default) is 'Daily digest of Model Context Protocol mentions'. So the mcp homepage tagline text changes from '...discussions from Bluesky' to '...mentions'. context.md states the mcp collection must reproduce today's behavior exactly, and unlike the nav-brand 'Bluesky ' drop this tagline change was not logged as a deviation. If exact reproduction is intended, set mcp.yaml's site_tagline (or the homepage default) to the original text; otherwise confirm the change is acceptable.", "file": "src/templates/homepage.html", "severity": "low"}]

## Contract
- Finish by running `git commit` so pre-commit hooks execute. No `--no-verify`. Do NOT push.
- If a finding is wrong or unfixable, skip it and say why in `deviations`.

## Report
Return ONLY this JSON:
{"commit_shas": ["..."], "summary": "one sentence", "deviations": ["..."], "unresolved_issues": ["..."]}
