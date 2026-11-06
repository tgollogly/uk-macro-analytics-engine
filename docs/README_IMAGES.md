# README images (GitHub rendering)

Hero and architecture bitmaps live at the repository root with **versioned basenames**: `hero-README-v2.png`, `architecture-README-v2.png` (plus matching **WebP** files). The numeric segment is bumped when we need to **break stale Camo/CDN caches** without changing image bytes twice.

GitHub’s HTML sanitizer **proxies** `<img>` requests through `camo.githubusercontent.com`, which fetches from `raw.githubusercontent.com/<owner>/<repo>/<ref>/<path>`. **Tap-to-open** uses `./<path>` and resolves to the **blob** viewer for the **same ref** as the README.

## Root cause post-mortem (why “fixes” failed)

1. **`?v=` cache busting** — Many READMEs use `hero.png?v=3`. Camo requests **`raw.githubusercontent.com/.../hero.png`** — the **query string is not part of the raw path**, so `?v=` does **not** change the fetched bytes. Prefer **new commits** (new bytes) or a **new filename** (new path everywhere).
2. **Same path for embed and blob** — Use `<a href="./hero-README-v2.png"><img src="./hero-README-v2.png" …>` so **display** and **full-size** both name **one** object on **this branch/PR**. Do not mix `./` with `https://github.com/ORG/REPO/blob/main/...` while developing — that jumps to `main`.
3. **Stale Camo vs fresh raw** — If users still see an old bitmap after a content-only push, **rename** the file (e.g. v2 → v3) and update README + `tools/regen_readme_images.py` constants so Camo’s URL changes.
4. **Legibility** — README column is ~**900px** wide on desktop; posters are ~2400px wide. The generator uses **measured wrapping + dynamic font scaling** so text stays inside cards.
5. **Preview files** — CI/agents may write `/opt/cursor/artifacts/readme-hero-{375,900,2400}px.png` for review (not committed).

## Common pitfalls

1. **Query strings** — Treat `?v=` as **cosmetic** for raw GitHub assets; prefer **commits** that change bytes or paths.
2. **Relative paths** — Use `./hero-README-v2.png` from `README.md` so **images and taps** resolve on **branches and PRs**.
3. **`tools/source/` copies** — `python3 tools/regen_readme_images.py` syncs **`tools/source/hero-README-v2.png`** / **`tools/source/architecture-README-v2.png`** to match the root PNGs.
4. **Case and filenames** — Use **lowercase** and hyphenated names to match Linux and GitHub URLs.

## Regenerate

```bash
pip install -r requirements.txt   # includes pillow
python3 tools/regen_readme_images.py
```

## Reproducible checks

- `tests/test_readme_assets.py` — PNG bytes present, magic header, root vs `tools/source/` identical.
- `tests/test_readme_github_links.py` — every wrapped README image has **matching** `href` and `src` for each `./…-README-v2.png`.

## Manual verification (human or browser)

After pushing a branch, on the GitHub **README** tab: (1) images load, (2) **tap** each image → lands on `…/blob/<branch>/hero-README-v2.png` (or architecture), (3) **Open raw** shows **image/png** bytes **identical** to a `curl` of `raw.githubusercontent.com/.../<same-ref>/hero-README-v2.png`. This environment cannot drive github.com in a logged-in session; use these steps locally for final sign-off.
