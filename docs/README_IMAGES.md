# README images (GitHub rendering)

Hero and architecture bitmaps live at the repository root: `hero.png`, `architecture.png` (plus WebP variants). GitHub’s Markdown renderer **proxies** images through `camo.githubusercontent.com`, which fetches the underlying object from `raw.githubusercontent.com/<owner>/<repo>/<ref>/hero.png`.

## Root cause post-mortem (why “fixes” failed)

1. **`?v=` cache busting** — Many READMEs use `hero.png?v=3`. GitHub’s Camo layer requests **`raw.githubusercontent.com/.../hero.png`** — the **query string is not part of the raw path**, so `?v=` does **not** change the fetched bytes or the ETag. If the image looked “stuck”, the real fix is **new PNG bytes in git** (or a **renamed file**), not a query param.
2. **“Open image” / wrong branch** — A bare `<img src="./hero.png">` (no parent `<a>`) opens via Camo or defaults in ways people find confusing on mobile. Wrapping with `<a href="./hero.png">` opens the **blob viewer on the current branch or PR** (same `./` resolution as the README). **Do not** use `https://github.com/ORG/REPO/blob/main/hero.png` while developing on another branch — that always jumps to `main`.
3. **Legibility** — README content column is ~**900px** wide on desktop; a 2400px-wide poster is scaled down ~2.6×. If labels are too small in the generator, text looks mushy. Increase font sizes in `tools/regen_readme_images.py` (this repo targets “v7” scale).

## Common pitfalls

1. **Query strings** — Treat `?v=` as **cosmetic** for raw GitHub assets; prefer **commits** that change bytes.
2. **Relative paths** — Use `./hero.png` from `README.md` so **images and taps** resolve on **branches and PRs**.
3. **`tools/source/` copies** — `python3 tools/regen_readme_images.py` syncs **`tools/source/hero.png`** / **`tools/source/architecture.png`** to match the root PNGs (avoids stale “source” previews).
4. **Case and filenames** — Use lowercase `hero.png` / `architecture.png` to match Linux and GitHub URLs.

## Regenerate

```bash
pip install -r requirements.txt   # includes pillow
python3 tools/regen_readme_images.py
```

## Reproducible checks

- `tests/test_readme_assets.py` — PNG bytes present, magic header, root vs `tools/source/` identical.
- `tests/test_readme_github_links.py` — every wrapped README image has **matching** `href` and `src` for `./hero.png` / `./architecture.png`.

## Manual verification (human or browser)

After pushing a branch, on the GitHub **README** tab: (1) images load, (2) **tap** each image → lands on `…/blob/<branch>/hero.png` (not a 404 HTML page), (3) **Open raw** or download shows **image/png** bytes. This environment cannot drive github.com in a logged-in session; use these steps locally for final sign-off.
