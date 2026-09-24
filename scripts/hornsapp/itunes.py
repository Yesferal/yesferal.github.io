"""iTunes / Apple Music helpers for HornsApp best-albums pages (build time).

This module runs when generating HTML (via sync-best-albums.py). It does NOT
call the iTunes API itself.

Responsibilities:
  - Emit cover <img> slots with data-cover-artist / data-cover-album
    (optional data-cover-year for the browser lookup)
  - Emit a hidden Apple Music <a> placeholder (class album-listen-apple)
  - Compose the listen row (Spotify link from spotify.py + Apple placeholder)
  - Point pages at the client script: hornsapp/best/album/itunes.js

Runtime (browser) work — covers + real Apple Music URLs — lives in itunes.js.
Spotify search URLs are build-time only; see spotify.py.
"""

from __future__ import annotations

import html

import spotify

FALLBACK_COVER = "/images/hornsapp.png"
SCRIPT_SRC = "/hornsapp/best/album/itunes.js?v=6"


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def apple_link_placeholder() -> str:
    """Hidden until itunes.js fills href from Search API. Icon + aria-label."""
    icon = """<svg class="album-listen-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M19.5 2.25a.75.75 0 0 0-.78-.05l-8.25 4.5A.75.75 0 0 0 10 7.5v6.63a3.25 3.25 0 1 0 1.5 2.62V8.4l7.5-4.09v7.82a3.25 3.25 0 1 0 1.5 2.62V3a.75.75 0 0 0-1-.75zM7.75 18.5a1.75 1.75 0 1 1 0-3.5 1.75 1.75 0 0 1 0 3.5zm9.5-2.25a1.75 1.75 0 1 1 0-3.5 1.75 1.75 0 0 1 0 3.5z"/></svg>"""
    return (
        '<a class="album-listen-apple" hidden '
        'target="_blank" rel="noopener noreferrer" '
        f'aria-label="Listen on Apple Music" title="Apple Music">{icon}</a>'
    )


def listen_row(artist: str, title: str, *, indent: str = "              ") -> str:
    """Spotify (build-time) + Apple Music (filled by itunes.js)."""
    return (
        f"{indent}<p class=\"album-listen\">\n"
        f"{indent}  {spotify.link_html(artist, title)}\n"
        f"{indent}  {apple_link_placeholder()}\n"
        f"{indent}</p>"
    )


def cover_anchor(
    *,
    artist: str,
    title: str,
    size: int = 96,
    loading: str = "lazy",
    extra_class: str = "",
    year: str | int | None = None,
) -> str:
    """Cover slot; itunes.js loads artwork (or HornsApp fallback)."""
    a = esc(artist)
    t = esc(title)
    cls = f"album-cover {extra_class}".strip()
    year_attr = ""
    if year not in (None, "", "?"):
        year_attr = f' data-cover-year="{esc(str(year))}"'
    return (
        f'<a class="{cls}" aria-hidden="true" tabindex="-1">'
        f'<img alt="" loading="{loading}" decoding="async" '
        f'data-cover-artist="{a}" data-cover-album="{t}"{year_attr} '
        f'width="{size}" height="{size}">'
        f"</a>"
    )


def script_tag() -> str:
    return f'<script src="{SCRIPT_SRC}"></script>'
