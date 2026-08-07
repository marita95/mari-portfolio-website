# mari.im — Jekyll site

A clean, hand-built **Jekyll** theme that mirrors the look and structure of
[mari.im](https://mari.im): centered logo + overlay menu, Vollkorn headings,
Fira Code body text, square-tile photo galleries with a lightbox, and a blog.
No WordPress, no plugins — just standard Jekyll, so GitHub Pages builds it
automatically when you push.

## How it's organised

```
_config.yml            site settings (title, collections, permalinks)
Gemfile                pins Jekyll to GitHub Pages' version for local preview
_layouts/              default, home, page, post, gallery
_includes/             head, header (logo + menu), footer, gallery-tiles, lightbox
_data/navigation.yml   the menu links (About / Blog / Photos)
assets/css/main.css    all styling (plain CSS — no Sass, builds anywhere)
assets/js/main.js      menu overlay + lightbox (vanilla JS)
assets/fonts/          Vollkorn + Fira Code (self-hosted, SIL OFL)
assets/images/         logo, gallery photos, blog images
_galleries/*.md        one file per photo gallery (front-matter image lists)
_posts/*.html          blog posts (vignettes)
index.html             home page
photos.html  blog.html about.html  404.html
CNAME                  custom domain for GitHub Pages
```

## Edit your content

- **Add a photo gallery** — create `_galleries/<name>.md`:
  ```yaml
  ---
  title: Roadtrips
  order: 7
  cover: /assets/images/galleries/roadtrips/cover.jpg
  images:
    - src: /assets/images/galleries/roadtrips/01.jpg
      alt: "Optional caption"
    - src: /assets/images/galleries/roadtrips/02.jpg
  ---
  ```
  It automatically appears at `/roadtrips/` and as a tile on the home/Photos page
  (ordered by `order`).

- **Write a blog post** — add `_posts/YYYY-MM-DD-title.md` (Markdown) or `.html`:
  ```
  ---
  layout: post
  title: "My title"
  date: 2026-06-24 12:00:00 +0000
  categories: vignettes
  ---
  Your content here…
  ```

- **Menu links** live in `_data/navigation.yml`. **Site title / tagline** live in
  `_config.yml`.

- **Substack posts** — they appear in the `/blog/` list automatically, mixed in
  with the vignettes and sorted by date. They live in `_substack/` (one small
  file per post, generated — don't hand-edit) and link straight to Substack.

  To pull in new posts:

  ```bash
  ./tools/refresh_substack.sh
  ```

  That fetches the feed and, if there's anything new, commits and pushes it.

  There's also a daily GitHub Action (`.github/workflows/substack.yml`) that
  tries to do this for you. It often can't: **Substack returns 403 to GitHub's
  servers**, so scheduled runs usually skip with a warning instead of updating.
  The same request works fine from your own computer, which is why the script
  above exists. Nothing is ever lost when a run is blocked — existing posts stay
  put. To have your Mac do it daily, schedule it while you're logged in:

  ```bash
  echo "0 9 * * * cd $PWD && ./tools/refresh_substack.sh >> /tmp/substack.log 2>&1" | crontab -
  ```

- **Image quality** — always add the full-resolution original; the theme never
  downsizes, so whatever you upload is what's served. To replace a photo with a
  sharper version, upload it over the old file (same name) or point the `src:` /
  `cover:` at the new file. (The home-page tiles use each gallery's `cover:`.)

## Preview locally

```bash
cd mari-jekyll
bundle install      # first time only
bundle exec jekyll serve
# open http://localhost:4000
```

## Deploy on GitHub Pages

1. Push this folder to a GitHub repo.
2. **Settings → Pages → Source: Deploy from a branch**, branch `main`, folder `/`.
   GitHub builds the Jekyll site for you (no Actions needed).
3. The `CNAME` file sets the custom domain to `mari.im`. Point your Namecheap DNS
   at GitHub Pages (apex `A` records `185.199.108–111.153`, and `www` CNAME →
   `<username>.github.io`), then tick **Enforce HTTPS**.

> Using a different domain? Edit `CNAME`, or delete it to use the
> `<username>.github.io` URL — in that case also set `baseurl: "/<repo-name>"`
> in `_config.yml` so asset paths resolve.

## Fonts

Vollkorn and Fira Code are licensed under the SIL Open Font License and are
self-hosted in `assets/fonts/`.
