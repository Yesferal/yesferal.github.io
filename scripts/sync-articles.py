#!/usr/bin/env python3
"""Sync article lists and sitemap from articles/catalog.json.

Committed HTML/sitemap keep empty markers. CI fills them at deploy time.
For local preview: python3 scripts/sync-articles.py
Before commit:     python3 scripts/sync-articles.py --clean
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "articles" / "catalog.json"

HOME_PATH = ROOT / "index.html"
ARTICLES_INDEX_PATH = ROOT / "articles" / "index.html"
SITEMAP_PATH = ROOT / "sitemap.xml"

MONTHS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def format_display_date(iso_date: str) -> str:
    year, month, day = iso_date.split("-")
    return f"{MONTHS[int(month) - 1]} {int(day)}, {year}"


def meta_line(article: dict) -> str:
    return (
        f"{format_display_date(article['date'])} · "
        f"{article['readMinutes']} min · {article['platform']}"
    )


def tags_html(tags: list[str], indent: str = "            ") -> str:
    lines = [f'{indent}<div class="tags">']
    lines.extend(f'{indent}    <span class="tag">{esc(tag)}</span>' for tag in tags)
    lines.append(f"{indent}</div>")
    return "\n".join(lines)


def published_sorted(catalog: dict) -> list[dict]:
    return sorted(
        catalog["published"],
        key=lambda a: (a["date"], a["slug"]),
        reverse=True,
    )


def home_limit(catalog: dict) -> int:
    limit = catalog.get("homeLimit", 5)
    if not isinstance(limit, int) or limit < 1:
        raise SystemExit("catalog.json homeLimit must be a positive integer")
    return limit


def render_home_cta(total: int, limit: int) -> str:
    """Show 'See all' only once the homepage would hide articles."""
    if total > limit:
        return '        <a href="/articles/">See all articles →</a>'
    return '        <a href="/articles/#coming-soon">Coming soon →</a>'


def render_home_cards(articles: list[dict]) -> str:
    blocks = []
    for article in articles:
        href = f"/articles/{article['slug']}/"
        blocks.append(
            f'''                <a class="article-card carousel-item" href="{esc(href)}">
                    <p class="meta">{esc(meta_line(article))}</p>
                    <h3>{esc(article["title"])}</h3>
                    <p>{esc(article["summary"])}</p>
{tags_html(article["tags"], indent="                    ")}
                </a>'''
        )
    return "\n".join(blocks)


def render_published_grid(articles: list[dict]) -> str:
    blocks = []
    for article in articles:
        href = f"/articles/{article['slug']}/"
        tag_lines = "\n".join(
            f'                <span class="tag">{esc(tag)}</span>'
            for tag in article["tags"]
        )
        blocks.append(
            f'''        <a class="article-card" href="{esc(href)}">
            <p class="meta">{esc(meta_line(article))}</p>
            <h3>{esc(article["title"])}</h3>
            <p>{esc(article["summary"])}</p>
            <div class="tags">
{tag_lines}
            </div>
        </a>'''
        )
    return "\n".join(blocks)


def render_coming_soon_grid(items: list[dict]) -> str:
    blocks = []
    for item in items:
        tags = "".join(f'<span class="tag">{esc(tag)}</span>' for tag in item["tags"])
        blocks.append(
            f'''        <div class="article-card article-card--soon">
            <p class="meta">{esc(item["meta"])}</p>
            <h3>{esc(item["title"])}</h3>
            <p>{esc(item["summary"])}</p>
            <div class="tags">{tags}</div>
        </div>'''
        )
    return "\n".join(blocks)


def render_sitemap_article_urls(articles: list[dict], site_url: str) -> str:
    blocks = []
    for article in articles:
        loc = f"{site_url.rstrip('/')}/articles/{article['slug']}/"
        blocks.append(
            f"""  <url>
    <loc>{esc(loc)}</loc>
    <lastmod>{esc(article["date"])}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>"""
        )
    return "\n".join(blocks)


def replace_marker(content: str, name: str, body: str) -> str:
    pattern = re.compile(
        rf"(<!--\s*articles:{re.escape(name)}:start\s*-->)"
        rf"(.*?)"
        rf"(<!--\s*articles:{re.escape(name)}:end\s*-->)",
        re.DOTALL | re.IGNORECASE,
    )
    if body:
        replacement = rf"\1\n{body}\n\3"
    else:
        replacement = r"\1\n\3"
    new_content, count = pattern.subn(replacement, content, count=1)
    if count != 1:
        raise SystemExit(f"Expected exactly one articles:{name} marker pair, found {count}")
    return new_content


def latest_article_date(articles: list[dict]) -> str:
    if not articles:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return max(a["date"] for a in articles)


def patch_sitemap_lastmod(content: str, latest: str) -> str:
    """Update lastmod on the home and /articles/ entries only."""
    # First two lastmod tags in the static section
    count = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        if count <= 2:
            return f"<lastmod>{latest}</lastmod>"
        return match.group(0)

    return re.sub(r"<lastmod>[^<]+</lastmod>", repl, content)


def load_catalog() -> dict:
    with CATALOG_PATH.open(encoding="utf-8") as handle:
        catalog = json.load(handle)
    for key in ("published", "comingSoon", "siteUrl"):
        if key not in catalog:
            raise SystemExit(f"catalog.json missing required key: {key}")
    for article in catalog["published"]:
        required = ("slug", "title", "summary", "date", "readMinutes", "platform", "tags")
        missing = [field for field in required if field not in article]
        if missing:
            raise SystemExit(f"Published article missing fields {missing}: {article}")
        page = ROOT / "articles" / article["slug"] / "index.html"
        if not page.is_file():
            raise SystemExit(f"Missing article page for slug '{article['slug']}': {page}")
    return catalog


def write_if_changed(path: Path, content: str) -> bool:
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    if existing == content:
        return False
    path.write_text(content, encoding="utf-8")
    print(f"Updated {path.relative_to(ROOT)}")
    return True


def apply_generated(home: str, articles_index: str, sitemap: str, catalog: dict, articles: list[dict], coming_soon: list[dict]) -> tuple[str, str, str]:
    limit = home_limit(catalog)
    home_articles = articles[:limit]
    home = replace_marker(home, "carousel", render_home_cards(home_articles))
    home = replace_marker(home, "home-cta", render_home_cta(len(articles), limit))
    articles_index = replace_marker(
        articles_index, "published", render_published_grid(articles)
    )
    articles_index = replace_marker(
        articles_index, "coming-soon", render_coming_soon_grid(coming_soon)
    )
    sitemap = replace_marker(
        sitemap,
        "urls",
        render_sitemap_article_urls(articles, catalog["siteUrl"]),
    )
    sitemap = patch_sitemap_lastmod(sitemap, latest_article_date(articles))
    return home, articles_index, sitemap


def apply_clean(home: str, articles_index: str, sitemap: str) -> tuple[str, str, str]:
    home = replace_marker(home, "carousel", "")
    home = replace_marker(
        home, "home-cta", '        <a href="/articles/#coming-soon">Coming soon →</a>'
    )
    articles_index = replace_marker(articles_index, "published", "")
    articles_index = replace_marker(articles_index, "coming-soon", "")
    sitemap = replace_marker(sitemap, "urls", "")
    return home, articles_index, sitemap


def markers_are_empty(content: str, name: str) -> bool:
    pattern = re.compile(
        rf"<!--\s*articles:{re.escape(name)}:start\s*-->"
        rf"(.*?)"
        rf"<!--\s*articles:{re.escape(name)}:end\s*-->",
        re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(content)
    if not match:
        raise SystemExit(f"Missing articles:{name} markers")
    body = match.group(1).strip()
    if name == "home-cta":
        # Default CTA is allowed in the committed template.
        return body in (
            "",
            '<a href="/articles/#coming-soon">Coming soon →</a>',
        )
    return body == ""


def sync(*, clean: bool = False, check: bool = False) -> int:
    catalog = load_catalog()
    articles = published_sorted(catalog)
    coming_soon = catalog["comingSoon"]

    home = HOME_PATH.read_text(encoding="utf-8")
    articles_index = ARTICLES_INDEX_PATH.read_text(encoding="utf-8")
    sitemap = SITEMAP_PATH.read_text(encoding="utf-8")

    if check:
        ok = True
        for path, name in (
            (HOME_PATH, "carousel"),
            (HOME_PATH, "home-cta"),
            (ARTICLES_INDEX_PATH, "published"),
            (ARTICLES_INDEX_PATH, "coming-soon"),
            (SITEMAP_PATH, "urls"),
        ):
            text = path.read_text(encoding="utf-8")
            if not markers_are_empty(text, name):
                print(f"NOT CLEAN: {path.relative_to(ROOT)} still has generated articles:{name} content")
                ok = False
        if not ok:
            print("Run: python3 scripts/sync-articles.py --clean")
            return 1
        print("Markers are empty (catalog is source of truth; CI fills at deploy)")
        return 0

    if clean:
        home, articles_index, sitemap = apply_clean(home, articles_index, sitemap)
    else:
        home, articles_index, sitemap = apply_generated(
            home, articles_index, sitemap, catalog, articles, coming_soon
        )

    changed = False
    changed |= write_if_changed(HOME_PATH, home)
    changed |= write_if_changed(ARTICLES_INDEX_PATH, articles_index)
    changed |= write_if_changed(SITEMAP_PATH, sitemap)

    if not changed:
        print("No file changes")
    elif not clean:
        limit = home_limit(catalog)
        print(f"Homepage shows up to {limit} articles ({len(articles)} published)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clear generated lists (empty markers) so only catalog.json is committed.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if marker regions are not empty (generated content left in the repo).",
    )
    args = parser.parse_args()
    if args.clean and args.check:
        raise SystemExit("Use either --clean or --check, not both")
    return sync(clean=args.clean, check=args.check)


if __name__ == "__main__":
    sys.exit(main())
