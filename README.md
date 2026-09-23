# Yesferal

Personal site for [yesferal.com](https://yesferal.com/) — mobile apps, articles, and about.  
Hosted on **GitHub Pages** via **GitHub Actions**.

## Repo layout

| Path | Role |
|------|------|
| `index.html` | Homepage (apps, articles carousel, about) |
| `articles/` | Articles (catalog, listing, each slug) |
| `hornsapp/` | HornsApp microsites (e.g. best albums) |
| `tumatch/` | TuMatch landing |
| `scripts/articles/` | Article sync tools |
| `scripts/hornsapp/` | HornsApp sync / CSV import |
| `styles.css`, `theme.js`, `images/` | Shared site chrome |
| `sitemap.xml` | Sitemap (article URLs filled at deploy) |
| `CNAME` | Custom domain (`yesferal.com`) |
| `.github/workflows/deploy-pages.yml` | Build + deploy |

## Articles

### Source of truth

Edit **`articles/catalog.json`** only for published cards and coming-soon items.

`homeLimit` (default `5`) controls how many latest articles appear on the homepage carousel. While you have fewer than that, the home link stays **Coming soon →**. Once you publish more than `homeLimit`, the carousel shows only the latest N and the link becomes **See all articles →**. `/articles/` always lists everything.

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

**Also read links:** only point to **older** articles (or peers already published). Do **not** edit an old article’s footer when a newer one ships — that creates noise diffs. The new article links back; older pages stay frozen.

### Sync script

```bash
# Local preview — fills markers in your working tree (do not commit)
python3 scripts/articles/sync.py

# Clear markers before commit
python3 scripts/articles/sync.py --clean

# Fail if generated content was left in the repo
python3 scripts/articles/sync.py --check
```

### Local preview

```bash
python3 scripts/articles/sync.py
python3 -m http.server 8766
# open http://127.0.0.1:8766/
python3 scripts/articles/sync.py --clean   # before committing
```

## HornsApp · Best albums

Personal year rankings at `/hornsapp/best/album/` (e.g. `/hornsapp/best/album/1980/`).

**How to update:** see [`hornsapp/best/README.md`](hornsapp/best/README.md).

| Path | Role |
|------|------|
| `hornsapp/best/album/catalog.json` | **Source of truth** (commit this) |
| `scripts/hornsapp/data/best-albums.csv` | Optional Sheet export (gitignored; not required) |
| `scripts/hornsapp/import-best-albums-csv.py` | CSV → catalog.json |
| `scripts/hornsapp/sync-best-albums.py` | catalog → year pages (**gitignored**; CI regenerates) |

Full steps: [`hornsapp/best/README.md`](hornsapp/best/README.md).

```bash
# After downloading the Sheet CSV into scripts/hornsapp/data/best-albums.csv
python3 scripts/hornsapp/import-best-albums-csv.py scripts/hornsapp/data/best-albums.csv
python3 scripts/hornsapp/sync-best-albums.py
# commit catalog.json only, then push
```

Later, `hornsapp.yesferal.com` can point at the same Pages site (DNS CNAME); paths can stay under `/hornsapp/…` or be redirected.

## Deploy (GitHub Pages + Actions)

On every push to `main` (and via **workflow_dispatch**), `.github/workflows/deploy-pages.yml`:

1. Runs `python3 scripts/articles/sync.py`
2. Runs `python3 scripts/hornsapp/sync-best-albums.py`
3. Packages the repo into a deploy artifact (excludes `scripts/`)
4. Deploys to GitHub Pages

### One-time Pages setting

Repo → **Settings** → **Pages** → **Build and deployment** → **Source**:

- Select **GitHub Actions** (not “Deploy from a branch”)
- Keep custom domain **yesferal.com** and **Enforce HTTPS**

Leave the `github-pages` environment as-is; the workflow uses it. Old entries under **Deployments** are history only — no need to turn them off.

## Site integrations (use cases)

These public configs connect **yesferal.com** to DNS, ads, and store listings. Values below are meant to be public (DNS and `app-ads.txt` are crawlable by design).

### Custom domain (DNS)

**Use case:** Point `yesferal.com` / `www` at GitHub Pages.

GoDaddy (or any DNS host):

```
Type: A      Name: @     Value: 185.199.108.153
Type: A      Name: @     Value: 185.199.109.153
Type: A      Name: @     Value: 185.199.110.153
Type: A      Name: @     Value: 185.199.111.153
Type: CNAME  Name: www   Value: yesferal.github.io
```

Also keep `CNAME` in the repo and **Enforce HTTPS** in Pages settings. The deploy artifact must include that `CNAME` file.

### AdMob (`app-ads.txt`)

**Use case:** Authorize Google to sell ads for apps that list this site as the developer website.

Root file `app-ads.txt` must stay at `https://yesferal.com/app-ads.txt`:

```
google.com, pub-2957187797569353, DIRECT, f08c47fec0942fa0
```

(Value from the AdMob account.)

### Google Play Console

**Use case:** Set the Play Store “Website” / developer site so listings and `app-ads.txt` checks resolve to this domain.

In Play Console: **Grow users → Store presence → Store settings → Website** → `https://yesferal.com/`
