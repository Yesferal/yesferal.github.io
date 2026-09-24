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
    """Icon link that opens Spotify search in a new tab."""
    href = esc(search_url(artist, title))
    icon = (
        '<svg class="album-listen-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
        '<path fill="currentColor" d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 '
        "12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101"
        "-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 "
        "8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3"
        "-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021"
        ".6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 "
        "8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 "
        '3.99-1.24 10.74-.941 14.94 1.561.479.28.599 1.02.3 1.42-.24.421-.84.599-1.26.3z"/>'
        "</svg>"
    )
    return (
        f'<a class="album-listen-spotify" href="{href}" '
        f'target="_blank" rel="noopener noreferrer" '
        f'aria-label="Listen on Spotify" title="Spotify">{icon}</a>'
    )
