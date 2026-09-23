#!/usr/bin/env python3
"""Generate HornsApp best-album static pages from catalog.json.

Usage:
  python3 scripts/hornsapp/sync-best-albums.py
  python3 scripts/hornsapp/import-best-albums-csv.py path/to.csv
"""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALBUM_ROOT = ROOT / "hornsapp" / "best" / "album"
CATALOG = ALBUM_ROOT / "catalog.json"


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def album_row(a: dict, *, bonus: bool = False) -> str:
    rank = a.get("rank") or "?"
    rank_label = "B" if str(rank).upper() == "B" else str(rank)
    title = esc(a.get("title") or "")
    artist = esc(a.get("artist") or "")
    track = (a.get("track") or "").strip()
    genre = (a.get("genre") or "").strip()
    have = bool(a.get("haveIt"))
    meta_bits = []
    if genre:
        meta_bits.append(esc(genre))
    if track and track != "?":
        meta_bits.append(f"pick: {esc(track)}")
    meta = " · ".join(meta_bits)
    have_badge = '<span class="album-have" title="In collection">owned</span>' if have else ""
    kind = "bonus" if bonus else "top"
    return f"""          <li class="album-item album-{kind}">
            <span class="album-rank">{esc(rank_label)}</span>
            <div class="album-body">
              <p class="album-title">{title}{have_badge}</p>
              <p class="album-artist">{artist}</p>
              {f'<p class="album-meta">{meta}</p>' if meta else ''}
            </div>
          </li>"""


def page_shell(
    *,
    title: str,
    description: str,
    canonical: str,
    body: str,
    active_year: int | None = None,
) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <script>
      (function () {{
        const stored = localStorage.getItem("theme");
        const theme = stored || (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
        document.documentElement.setAttribute("data-theme", theme);
      }})();
    </script>
    <title>{esc(title)} | Yesferal</title>
    <meta name="description" content="{esc(description)}"/>
    <link rel="canonical" href="{esc(canonical)}"/>
    <meta property="og:title" content="{esc(title)}"/>
    <meta property="og:description" content="{esc(description)}"/>
    <meta property="og:type" content="website"/>
    <meta property="og:url" content="{esc(canonical)}"/>
    <meta property="og:image" content="https://yesferal.com/images/hornsapp.png"/>
    <link rel="icon" href="/favicon.ico" sizes="32x32">
    <link rel="icon" type="image/png" href="/favicon-32x32.png" sizes="32x32">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">
    <link rel="stylesheet" href="/styles.css">
    <link rel="stylesheet" href="/hornsapp/best/album/albums.css">
</head>
<body class="albums-page">
<nav class="nav">
    <a class="nav-brand" href="/">Yesferal</a>
    <div class="nav-actions">
        <button type="button" class="theme-toggle" id="theme-toggle" aria-label="Toggle theme">🌙</button>
        <div class="nav-links">
            <a href="/hornsapp/best/album/">Best albums</a>
            <a href="/">Apps</a>
        </div>
    </div>
</nav>
{body}
<footer>
    <div class="footer-links">
        <a href="https://play.google.com/store/apps/details?id=com.yesferal.hornsapp" rel="noopener">HornsApp on Play</a>
        <a href="/hornsapp/best/album/">All years</a>
        <a href="/">yesferal.com</a>
    </div>
    © 2026 Yesferal · Personal ranking
</footer>
<script src="/theme.js"></script>
</body>
</html>
"""


def year_nav(years: list[dict], current: int | None) -> str:
    links = []
    for y in years:
        yr = y["year"]
        cls = ' class="is-active"' if current == yr else ""
        links.append(f'<a href="/hornsapp/best/album/{yr}/"{cls}>{yr}</a>')
    return '<nav class="year-rail" aria-label="Years">' + "".join(links) + "</nav>"


def build_index(data: dict) -> None:
    years = data["years"]
    total = sum(y["count"] for y in years)
    cards = []
    for y in years:
        top_n = len(y.get("top") or [])
        bonus_n = len(y.get("bonus") or [])
        cards.append(
            f"""        <a class="year-card" href="/hornsapp/best/album/{y['year']}/">
          <span class="year-card-year">{y['year']}</span>
          <span class="year-card-meta">{y['count']} albums · top {top_n}{f' · +{bonus_n} bonus' if bonus_n else ''}</span>
        </a>"""
        )
    body = f"""
<main class="albums-wrap">
  <header class="albums-hero">
    <p class="albums-kicker">HornsApp</p>
    <h1>Best albums</h1>
    <p class="albums-lead">{esc(data.get('sourceNote') or '')}</p>
    <p class="albums-stats">{len(years)} years · {total} albums</p>
  </header>
  {year_nav(years, None)}
  <section class="year-grid" aria-label="Years">
{chr(10).join(cards)}
  </section>
</main>
"""
    html_out = page_shell(
        title="HornsApp · Best albums",
        description="Personal best albums by year — top picks and bonus records.",
        canonical="https://yesferal.com/hornsapp/best/album/",
        body=body,
    )
    (ALBUM_ROOT / "index.html").write_text(html_out, encoding="utf-8")


def build_year(data: dict, year_block: dict) -> None:
    year = year_block["year"]
    years = data["years"]
    top = year_block.get("top") or []
    bonus = year_block.get("bonus") or []
    idx = next(i for i, y in enumerate(years) if y["year"] == year)
    prev_y = years[idx - 1]["year"] if idx > 0 else None
    next_y = years[idx + 1]["year"] if idx < len(years) - 1 else None

    top_html = "\n".join(album_row(a) for a in top) or "          <li class=\"album-empty\">No top albums listed.</li>"
    bonus_section = ""
    if bonus:
        bonus_html = "\n".join(album_row(a, bonus=True) for a in bonus)
        bonus_section = f"""
  <section class="album-section">
    <h2>Bonus</h2>
    <p class="section-note">Ranks 7+ and <strong>B</strong> — extras beyond the main six.</p>
    <ol class="album-list album-list-bonus">
{bonus_html}
    </ol>
  </section>"""

    pager = ['<div class="year-pager">']
    if prev_y:
        pager.append(f'<a class="btn" href="/hornsapp/best/album/{prev_y}/">← {prev_y}</a>')
    else:
        pager.append('<span></span>')
    pager.append('<a class="btn" href="/hornsapp/best/album/">All years</a>')
    if next_y:
        pager.append(f'<a class="btn" href="/hornsapp/best/album/{next_y}/">{next_y} →</a>')
    else:
        pager.append('<span></span>')
    pager.append("</div>")

    body = f"""
<main class="albums-wrap">
  <a class="crumb" href="/hornsapp/best/album/">← All years</a>
  <header class="albums-hero albums-hero-year">
    <p class="albums-kicker">HornsApp · Best albums</p>
    <h1>{year}</h1>
    <p class="albums-lead">{year_block['count']} albums this year · main list capped at 6</p>
  </header>
  {year_nav(years, year)}
  <section class="album-section">
    <h2>Top {len(top)}</h2>
    <ol class="album-list">
{top_html}
    </ol>
  </section>
{bonus_section}
  {''.join(pager)}
</main>
"""
    out_dir = ALBUM_ROOT / str(year)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(
        page_shell(
            title=f"Best albums {year} · HornsApp",
            description=f"Top albums of {year} — personal HornsApp ranking.",
            canonical=f"https://yesferal.com/hornsapp/best/album/{year}/",
            body=body,
            active_year=year,
        ),
        encoding="utf-8",
    )


def main() -> None:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    # prune old year folders that are no longer in catalog
    known = {str(y["year"]) for y in data["years"]}
    for child in ALBUM_ROOT.iterdir():
        if child.is_dir() and child.name.isdigit() and child.name not in known:
            for f in child.glob("*"):
                f.unlink()
            child.rmdir()

    build_index(data)
    for y in data["years"]:
        build_year(data, y)
    print(f"Wrote index + {len(data['years'])} year pages under hornsapp/best/album/")


if __name__ == "__main__":
    main()
