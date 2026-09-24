#!/usr/bin/env python3
"""Generate HornsApp best-album static pages from catalog.json.

Usage:
  python3 scripts/hornsapp/sync-best-albums.py
  python3 scripts/hornsapp/import-best-albums-csv.py path/to.csv

Listen / cover helpers (keep sync focused on page structure):
  scripts/hornsapp/spotify.py  — Spotify search links (build time only)
  scripts/hornsapp/itunes.py   — cover slots + Apple Music placeholders (build time)
  hornsapp/best/album/itunes.js — fetches covers + Apple Music URLs (browser)

Generated HTML (index + year folders) is gitignored; CI regenerates on deploy.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

import itunes
import spotify

ROOT = Path(__file__).resolve().parents[2]
ALBUM_ROOT = ROOT / "hornsapp" / "best" / "album"
CATALOG = ALBUM_ROOT / "catalog.json"


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def album_row(a: dict, *, bonus: bool = False, year: int | None = None) -> str:
    raw_title = a.get("title") or ""
    raw_artist = a.get("artist") or ""
    title = esc(raw_title)
    artist = esc(raw_artist)
    track = (a.get("track") or "").strip()
    genre = (a.get("genre") or "").strip()
    cover_year = a.get("debut") or year
    meta_bits = []
    if genre:
        meta_bits.append(f'<span class="album-genre">{esc(genre)}</span>')
    if track and track != "?":
        # "Pick" = favorite track on the album (same sense as AllMusic track picks)
        meta_bits.append(spotify.pick_html(raw_artist, track))
    meta = "".join(meta_bits)
    kind = "bonus" if bonus else "top"
    if bonus:
        marker = '<span class="album-rank album-rank-bonus" aria-hidden="true">✦</span>'
    else:
        rank = a.get("rank") or "?"
        rank_label = esc(str(rank))
        marker = f'<span class="album-rank">{rank_label}</span>'
    return f"""          <li class="album-item album-{kind}">
            {marker}
            <div class="album-body">
              <p class="album-title">{title}</p>
              <p class="album-artist">{artist}</p>
              {f'<p class="album-meta">{meta}</p>' if meta else ''}
{itunes.listen_row(raw_artist, raw_title)}
            </div>
            {itunes.cover_anchor(artist=raw_artist, title=raw_title, size=96, loading="lazy", year=cover_year)}
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
    <title>{esc(title)} | HornsApp</title>
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
    <link rel="stylesheet" href="/hornsapp/best/album/albums.css?v=22">
</head>
<body class="albums-page">
<nav class="nav">
    <a class="nav-brand" href="/hornsapp/">HornsApp</a>
    <div class="nav-actions">
        <button type="button" class="theme-toggle" id="theme-toggle" aria-label="Toggle theme">🌙</button>
    </div>
</nav>
{body}
<footer>
    © 2026 Yesferal · HornsApp
</footer>
<script src="/theme.js"></script>
{itunes.script_tag()}
<script>
(function () {{
  function centerActiveYear() {{
    var rail = document.querySelector(".year-rail");
    var active = rail && rail.querySelector("a.is-active");
    if (!rail || !active) return;
    var railRect = rail.getBoundingClientRect();
    var activeRect = active.getBoundingClientRect();
    var delta = (activeRect.left + activeRect.width / 2) - (railRect.left + railRect.width / 2);
    rail.scrollLeft += delta;
  }}
  requestAnimationFrame(function () {{
    requestAnimationFrame(centerActiveYear);
  }});
}})();
</script>
</body>
</html>
"""


def build_index(data: dict) -> None:
    years = data["years"]
    total = sum(y["count"] for y in years)
    cards = []
    for y in years:
        n = y["count"]
        label = "1 album" if n == 1 else f"{n} albums"
        cards.append(
            f"""        <a class="year-card" href="/hornsapp/best/album/{y['year']}/">
          <span class="year-card-year">{y['year']}</span>
          <span class="year-card-meta">{label}</span>
        </a>"""
        )
    body = f"""
<main class="albums-wrap">
  <div class="albums-hero">
    <div class="albums-hero-stack">
      <h1>Best albums</h1>
      <p class="albums-lead">{esc(data.get('sourceNote') or '')}</p>
      <p class="albums-stats">{len(years)} years · {total} albums</p>
    </div>
  </div>
  <section class="year-grid" aria-label="Years">
{chr(10).join(cards)}
  </section>
</main>
"""
    html_out = page_shell(
        title="Best albums",
        description="Personal best albums by year — ranked picks and honorable mentions.",
        canonical="https://yesferal.com/hornsapp/best/album/",
        body=body,
    )
    (ALBUM_ROOT / "index.html").write_text(html_out, encoding="utf-8")


def year_nav(years: list[dict], current: int | None) -> str:
    links = []
    for y in years:
        yr = y["year"]
        cls = ' class="is-active"' if current == yr else ""
        links.append(f'<a href="/hornsapp/best/album/{yr}/"{cls}>{yr}</a>')
    return '<nav class="year-rail" aria-label="Years">' + "".join(links) + "</nav>"


def build_year(data: dict, year_block: dict) -> None:
    year = year_block["year"]
    years = data["years"]
    top = year_block.get("top") or []
    bonus = year_block.get("bonus") or []
    idx = next(i for i, y in enumerate(years) if y["year"] == year)
    prev_y = years[idx - 1]["year"] if idx > 0 else None
    next_y = years[idx + 1]["year"] if idx < len(years) - 1 else None

    top_html = "\n".join(album_row(a, year=year) for a in top) or "          <li class=\"album-empty\">No top albums listed.</li>"
    bonus_section = ""
    if bonus:
        bonus_html = "\n".join(album_row(a, bonus=True, year=year) for a in bonus)
        bonus_section = f"""
  <section class="album-section album-section-bonus">
    <h2>Honorable mentions</h2>
    <p class="section-note">Albums we love just as much — kept here as favorites beyond the ranked list.</p>
    <ul class="album-list album-list-bonus">
{bonus_html}
    </ul>
  </section>"""

    pager = ['<div class="year-pager">']
    if prev_y:
        pager.append(f'<a class="btn store-btn" href="/hornsapp/best/album/{prev_y}/">← {prev_y}</a>')
    else:
        pager.append('<span></span>')
    pager.append('<a class="btn store-btn" href="/hornsapp/best/album/">All years</a>')
    if next_y:
        pager.append(f'<a class="btn store-btn" href="/hornsapp/best/album/{next_y}/">{next_y} →</a>')
    else:
        pager.append('<span></span>')
    pager.append("</div>")

    ranked_n = len(top)
    bonus_n = len(bonus)
    if bonus_n:
        stats = f"{ranked_n} ranked · {bonus_n} mentions"
    else:
        stats = f"{ranked_n} ranked" if ranked_n != 1 else "1 ranked"

    featured = ""
    if top:
        first = top[0]
        raw_title = first.get("title") or ""
        raw_artist = first.get("artist") or ""
        f_title = esc(raw_title)
        f_artist = esc(raw_artist)
        f_genre = (first.get("genre") or "").strip()
        f_track = (first.get("track") or "").strip()
        featured_meta = []
        if f_genre:
            featured_meta.append(esc(f_genre))
        if f_track and f_track != "?":
            featured_meta.append(spotify.pick_html(raw_artist, f_track))
        featured_meta_html = f'<p class="year-featured-meta">{" · ".join(featured_meta)}</p>' if featured_meta else ""
        featured_listen = itunes.listen_row(raw_artist, raw_title, indent="      ")
        featured_cover = itunes.cover_anchor(
            artist=raw_artist,
            title=raw_title,
            size=280,
            loading="eager",
            extra_class="year-featured-cover",
            year=first.get("debut") or year,
        )
        featured = f"""
  <div class="year-featured">
    <div class="year-featured-copy">
      <p class="year-featured-label">Album of the year</p>
      <p class="year-featured-title">{f_title}</p>
      <p class="year-featured-artist">{f_artist}</p>
      {featured_meta_html}
{featured_listen}
    </div>
    {featured_cover}
  </div>"""

    body = f"""
<main class="albums-wrap albums-wrap-year">
  <a class="crumb" href="/hornsapp/best/album/">← All years</a>
  <div class="albums-hero albums-hero-year">
    <div class="albums-hero-stack">
      <h1>{year}</h1>
      <p class="albums-stats">{stats}</p>
    </div>
  </div>
  {year_nav(years, year)}
{featured}
  <section class="album-section">
    <h2>Ranked</h2>
    <ol class="album-list album-list-top">
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
            title=f"Best albums {year}",
            description=f"Top albums of {year} — personal HornsApp ranking.",
            canonical=f"https://yesferal.com/hornsapp/best/album/{year}/",
            body=body,
            active_year=year,
        ),
        encoding="utf-8",
    )


def main() -> None:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
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
