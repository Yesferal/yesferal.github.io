# Article roadmap

Living list of topics for yesferal.com. One article per week when possible.

**Source of truth for the live site:** `articles/catalog.json`  

Do not hand-edit article cards in `index.html` / `articles/index.html` / `sitemap.xml` — those marker regions stay empty in git. CI fills them on deploy.

```bash
python3 scripts/sync-articles.py          # local preview
python3 scripts/sync-articles.py --clean  # clear markers before commit
```

## Published

See `catalog.json` → `published` (and the pages under `articles/<slug>/`).

Latest: CI/CD for a static site on GitHub Pages (`github-pages-actions-cicd`).

## Series — HornsApp architecture (next)

- [ ] From shared contract to SwiftUI — how the mapping layer works
- [ ] Navigation shared between iOS and Android
- [ ] One SwiftUI base, two apps — HornsApp and Muvin

## Worth learning next (future articles)

Topics to explore in depth — not replacing Clean Architecture / MVVM, but building on them.

- [ ] Jetpack Compose + UiState / MVI-style flows
- [ ] SwiftUI + Observation (`@Observable`) — modern state without boilerplate
- [ ] KMP in production — modularization and shared boundaries
- [ ] CI/CD for mobile — Fastlane, GitHub Actions, reliable releases
- [ ] Modular architecture at scale — feature modules and large codebases

## Notes

- Keep articles ~5 min read, architecture tone first.
- Add code in series part 2+ (mapping, navigation).
- Update `catalog.json` (published + comingSoon) when order or copy changes — do not hand-edit the article cards in `index.html` / `articles/index.html`.
