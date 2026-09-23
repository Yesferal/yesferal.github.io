#!/usr/bin/env python3
"""Rebuild hornsapp/best/album/catalog.json from a Google Sheets CSV export."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "hornsapp" / "best" / "album" / "catalog.json"


def clean_row(d: dict) -> dict:
    return {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in d.items()}


def rank_key(a: dict):
    r = a["rank"]
    if str(r).upper() == "B":
        return (1, 999)
    try:
        return (0, int(r))
    except ValueError:
        return (1, 998)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path, help="Sheet export CSV")
    args = parser.parse_args()

    by_year: dict[str, list] = defaultdict(list)
    with args.csv_path.open(encoding="utf-8-sig", newline="") as f:
        for raw in csv.DictReader(f):
            r = clean_row(raw)
            year = r.get("Year") or ""
            if not year.isdigit():
                continue
            by_year[year].append(
                {
                    "id": r.get("ID") or "",
                    "rank": r.get("#") or "",
                    "haveIt": (r.get("Have It") or "").upper() == "TRUE",
                    "title": r.get("Vinyl") or "",
                    "artist": r.get("Artist") or "",
                    "track": r.get("Song") or "",
                    "genre": r.get("Genre") or "",
                    "debut": r.get("Debut") or "",
                    "instrument": r.get("Instrument") or "",
                }
            )

    years = []
    for y in sorted(by_year.keys()):
        albums = sorted(by_year[y], key=rank_key)
        top = [a for a in albums if str(a["rank"]).isdigit() and 1 <= int(a["rank"]) <= 6]
        bonus = [
            a
            for a in albums
            if (str(a["rank"]).isdigit() and int(a["rank"]) >= 7) or str(a["rank"]).upper() == "B"
        ]
        years.append(
            {
                "year": int(y),
                "count": len(albums),
                "top": top,
                "bonus": bonus,
            }
        )

    payload = {
        "title": "Best albums",
        "brand": "HornsApp",
        "sourceNote": "Personal ranking by year. Top 6 are the main list; 7+ and B are bonus.",
        "years": years,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(years)} years, {sum(y['count'] for y in years)} albums)")


if __name__ == "__main__":
    main()
