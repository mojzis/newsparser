#!/usr/bin/env bash
# Daily run: collect -> fetch -> evaluate -> report, then publish the site to
# the gh-pages branch (GitHub Pages: https://mojzis.github.io/newsparser/).
# Run by the systemd user timer newsparser-daily.timer (05:15 local time).
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:$PATH"

REPO_URL="git@github.com:mojzis/newsparser.git"
BASE_PATH="/newsparser"
SITE_URL="https://mojzis.github.io/newsparser"
PAGES_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/newsparser-pages"
COLLECTION=mcp

uv run --frozen nsp run-all --collection "$COLLECTION" --max-posts 100 --days-back 7

# Assemble the site: collection pages at the root, shared pages alongside.
SITE="$(mktemp -d)"
trap 'rm -rf "$SITE"' EXIT
cp -r "output/$COLLECTION/." "$SITE/"
for f in output/*.html output/query output/metadata; do
    [ -e "$f" ] && cp -r "$f" "$SITE/"
done
touch "$SITE/.nojekyll"
# Project Pages are served under /newsparser/, so root-absolute links need the prefix.
find "$SITE" \( -name '*.html' -o -name '*.xml' \) -print0 |
    xargs -0 sed -i -E \
        -e "s#(href|src)=\"/#\1=\"$BASE_PATH/#g" \
        -e "s#https://example.com#$SITE_URL#g"

# Publish: single-commit-per-run history on gh-pages.
if [ ! -d "$PAGES_DIR/.git" ]; then
    git clone --quiet "$REPO_URL" "$PAGES_DIR"
fi
cd "$PAGES_DIR"
git fetch --quiet origin
if git rev-parse --verify --quiet origin/gh-pages >/dev/null; then
    git checkout --quiet -B gh-pages origin/gh-pages
else
    git checkout --quiet --orphan gh-pages
fi
git rm -rqf --ignore-unmatch . >/dev/null
cp -r "$SITE/." .
git add -A
if git diff --cached --quiet; then
    echo "No site changes."
else
    git commit --quiet -m "Site update $(date -u +%F)"
    git push --quiet origin gh-pages
    echo "Published to $SITE_URL"
fi
