"""iTunes / Apple Music helpers for HornsApp best-albums pages (build time).

This module runs when generating HTML (via sync-best-albums.py). It does NOT
call the iTunes API itself.

Responsibilities:
  - Emit cover <img> slots with data-cover-artist / data-cover-album
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
SCRIPT_SRC = "/hornsapp/best/album/itunes.js?v=1"


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def apple_link_placeholder() -> str:
    """Hidden until itunes.js fills href from Search API."""
    return (
        '<a class="album-listen-apple" hidden '
        'target="_blank" rel="noopener noreferrer">Apple Music</a>'
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
) -> str:
    """Cover slot; itunes.js loads artwork (or HornsApp fallback)."""
    a = esc(artist)
    t = esc(title)
    cls = f"album-cover {extra_class}".strip()
    return (
        f'<a class="{cls}" aria-hidden="true" tabindex="-1">'
        f'<img alt="" loading="{loading}" decoding="async" '
        f'data-cover-artist="{a}" data-cover-album="{t}" '
        f'width="{size}" height="{size}">'
        f"</a>"
    )


def script_tag() -> str:
    return f'<script src="{SCRIPT_SRC}"></script>'
