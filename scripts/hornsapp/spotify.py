"""Spotify helpers for HornsApp best-albums pages (build time).

This module only builds Spotify links when generating HTML. There is no
spotify.js — links are plain URLs in the page.

Why not the Spotify Web API?
  It needs OAuth / a client secret, which we avoid on a static GitHub Pages site.
  Instead we use public search deep links: open.spotify.com/search/...

Related:
  itunes.py  — cover slots + Apple Music placeholders (build time)
  itunes.js  — fetches covers + Apple Music album URLs (browser)
"""

from __future__ import annotations

import html
from urllib.parse import quote


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def search_url(artist: str, title: str) -> str:
    """Open Spotify search for artist + album (no API key)."""
    return "https://open.spotify.com/search/" + quote(f"{artist} {title}")


def link_html(artist: str, title: str) -> str:
    """Anchor that opens Spotify search in a new tab."""
    href = esc(search_url(artist, title))
    return (
        f'<a class="album-listen-spotify" href="{href}" '
        f'target="_blank" rel="noopener noreferrer">Spotify</a>'
    )
