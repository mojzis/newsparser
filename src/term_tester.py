"""Try search terms against sources before adding them to a collection.

Runs each term on each source, summarizes what comes back (volume, top domains,
co-occurring hashtags, sample posts) and renders one local HTML page. Bluesky search
needs a logged-in session and blocks cloud IPs, so this runs on your own machine with
the credentials from `.env`.
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.bluesky.client import BlueskyClient
from src.config.searches import SearchDefinition
from src.config.settings import Settings
from src.models.post import BlueskyPost
from src.sources.registry import SOURCE_FACTORIES

TEMPLATES_DIR = Path(__file__).parent / "templates"
TOP_N = 10
SAMPLE_SIZE = 8
SELF_HOSTS = {"bsky.app", "news.ycombinator.com"}
HN_PAGE_CAP = 1000  # Algolia returns at most this many hits per request


class BlueskyLoginError(Exception):
    """Bluesky login failed, so Bluesky can't be searched."""


@dataclass
class TermResult:
    """What one term returned from one source."""

    term: str
    source: str
    count: int
    max_posts: int
    oldest: datetime | None = None
    newest: datetime | None = None
    posts_per_day: float | None = None
    last_30_days: int = 0
    top_domains: list[tuple[str, int]] = field(default_factory=list)
    top_hashtags: list[tuple[str, int]] = field(default_factory=list)
    samples: list[BlueskyPost] = field(default_factory=list)

    @property
    def hit_cap(self) -> bool:
        """True when the source returned as many posts as asked for (volume is higher)."""
        return self.count >= self.max_posts


def post_url(post: BlueskyPost) -> str:
    """Link to the post on its source's website, or "" for an unknown source."""
    if post.source == "hackernews":
        return f"https://news.ycombinator.com/item?id={post.id.removeprefix('hn_')}"
    if post.source == "bluesky":
        # at://did:plc:xyz/app.bsky.feed.post/rkey
        rkey = post.id.rsplit("/", 1)[-1]
        return f"https://bsky.app/profile/{post.author}/post/{rkey}"
    return ""


def summarize(
    term: str, source: str, posts: list[BlueskyPost], max_posts: int, now: datetime
) -> TermResult:
    """Count volume, domains and hashtags for one term's posts."""
    result = TermResult(term=term, source=source, count=len(posts), max_posts=max_posts)
    if not posts:
        return result

    dates = [p.created_at for p in posts]
    result.oldest, result.newest = min(dates), max(dates)
    # A capped result only covers newest..oldest; an uncapped one is everything up to now.
    end = result.newest if result.hit_cap else now
    span = max(end - result.oldest, timedelta(hours=1))
    result.posts_per_day = round(len(posts) / (span.total_seconds() / 86400), 2)
    month_ago = now - timedelta(days=30)
    result.last_30_days = sum(1 for d in dates if d >= month_ago)

    domains = Counter(
        (urlparse(str(link)).hostname or "").removeprefix("www.")
        for p in posts
        for link in p.links
    )
    for host in ["", *SELF_HOSTS]:
        domains.pop(host, None)
    result.top_domains = domains.most_common(TOP_N)

    term_tag = term.lower().lstrip("#")
    hashtags = Counter(
        tag for p in posts for tag in p.tags if tag != term_tag and not tag.isdigit()
    )
    result.top_hashtags = hashtags.most_common(TOP_N)

    result.samples = sorted(
        posts,
        key=lambda p: p.engagement_metrics.likes + p.engagement_metrics.reposts,
        reverse=True,
    )[:SAMPLE_SIZE]
    return result


def term_definition(term: str) -> SearchDefinition:
    """A one-term search definition, as a collection would hold it."""
    return SearchDefinition(
        name=term, description=f"Term test: {term}", include_terms=[term]
    )


async def run_terms(
    terms: list[str], sources: list[str], max_posts: int, settings: Settings
) -> list[TermResult]:
    """Search every term on every source and summarize the results."""
    bluesky_client = BlueskyClient(settings)
    if "bluesky" in sources and not await bluesky_client.authenticate():
        raise BlueskyLoginError(
            "Bluesky login failed. Set BLUESKY_HANDLE and BLUESKY_APP_PASSWORD in .env."
        )
    built = {name: SOURCE_FACTORIES[name](settings, bluesky_client) for name in sources}
    now = datetime.now(UTC)
    results = []
    try:
        for term in terms:
            for name, source in built.items():
                posts = await source.search(term_definition(term), max_posts)
                results.append(summarize(term, name, posts, max_posts, now))
    finally:
        await bluesky_client.close()
    return results


def searches_yaml(terms: list[str]) -> str:
    """A `searches:` snippet to paste into a collection file."""
    searches: dict[str, dict] = {}
    for term in terms:
        base = "".join(c if c.isalnum() else "_" for c in term.lower()).strip("_")
        key, n = base or "term", 1
        while key in searches:
            n += 1
            key = f"{base or 'term'}_{n}"
        searches[key] = {
            "name": term,
            "description": f"Posts matching {term}",
            "include_terms": [term],
            "sort": "latest",
            "enabled": True,
        }
    return yaml.safe_dump(
        {"searches": {"searches": searches}}, sort_keys=False, allow_unicode=True
    )


def render_html(results: list[TermResult], terms: list[str]) -> str:
    """Render the results page."""
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape(["html"])
    )
    return env.get_template("term_tester.html").render(
        results=results,
        post_url=post_url,
        yaml_snippet=searches_yaml(terms),
        generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
    )
