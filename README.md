# Yesferal

Personal site for [yesferal.com](https://yesferal.com/) — mobile apps, articles, and about.  
Hosted on **GitHub Pages** via **GitHub Actions**.

## Repo layout

| Path | Role |
|------|------|
| `index.html` | Homepage (apps, articles carousel, about) |
| `articles/<slug>/index.html` | Full article pages |
| `articles/catalog.json` | **Source of truth** for article lists + coming soon |
| `articles/index.html` | Articles listing (markers filled at deploy) |
| `articles/ROADMAP.md` | Internal topic ideas |
| `scripts/sync-articles.py` | Fills homepage / articles index / sitemap from the catalog |
| `sitemap.xml` | Sitemap (article URLs filled at deploy) |
| `styles.css`, `theme.js` | Shared styles and light/dark theme |
| `CNAME` | Custom domain (`yesferal.com`) |
| `.github/workflows/deploy-pages.yml` | Build + deploy |

## Articles

### Source of truth

Edit **`articles/catalog.json`** only for published cards and coming-soon items.

Do **not** hand-edit article cards in:

- `index.html` (carousel)
- `articles/index.html` (published + coming soon)
- `sitemap.xml` (article URLs)

Those files keep **empty HTML/XML markers** in git. Actions fills them on every deploy so the live site is static HTML (better SEO).

### Catalog fields (published)

```json
{
  "slug": "my-article-slug",
  "title": "Title",
  "summary": "One or two sentences for the cards.",
  "date": "2026-09-02",
  "readMinutes": 5,
  "platform": "Android",
  "tags": ["Kotlin", "Android"]
}
```

`slug` must match a folder: `articles/<slug>/index.html`.

Coming-soon items use `title`, `summary`, `meta`, and `tags` (no `slug` until published).

### Add a new article

1. Create `articles/your-slug/index.html` (copy an existing article and edit).
2. Add an entry under `published` in `articles/catalog.json`.
3. Optional local preview (see below).
4. Commit **the article page + `catalog.json`** (keep markers empty).
5. Push to `main` — Actions syncs lists and deploys.

### Sync script

```bash
# Local preview — fills markers in your working tree (do not commit)
python3 scripts/sync-articles.py

# Clear markers before commit
python3 scripts/sync-articles.py --clean

# Fail if generated content was left in the repo
python3 scripts/sync-articles.py --check
```

### Local preview

```bash
python3 scripts/sync-articles.py
python3 -m http.server 8765
# open http://127.0.0.1:8765/
python3 scripts/sync-articles.py --clean   # before committing
```

## Deploy (GitHub Pages + Actions)

On every push to `main` (and via **workflow_dispatch**), `.github/workflows/deploy-pages.yml`:

1. Runs `python3 scripts/sync-articles.py`
2. Uploads the built site
3. Deploys to GitHub Pages

### One-time Pages setting

Repo → **Settings** → **Pages** → **Build and deployment** → **Source**:

- Select **GitHub Actions** (not “Deploy from a branch”)
- Keep custom domain **yesferal.com** and **Enforce HTTPS**

Leave the `github-pages` environment as-is; the workflow uses it. Old entries under **Deployments** are history only — no need to turn them off.

### Custom domain DNS (GoDaddy)

```
Type: A      Name: @     Value: 185.199.108.153
Type: A      Name: @     Value: 185.199.109.153
Type: A      Name: @     Value: 185.199.110.153
Type: A      Name: @     Value: 185.199.111.153
Type: CNAME  Name: www   Value: yesferal.github.io
```

Then set the custom domain in Pages settings and enable **Enforce HTTPS**.

## AdMob (`app-ads.txt`)

Root file `app-ads.txt` must stay published at `https://yesferal.com/app-ads.txt`:

```
google.com, pub-2957187797569353, DIRECT, f08c47fec0942fa0
```

(Value from the AdMob account.)

## Google Play Console

Store listing website: **Grow users → Store presence → Store settings → Website** → `https://yesferal.com/`
