# Story effects — reference mapping (read-only research, 2026-11-07)

**Source reviewed:** [Slider Revolution — cool website effects](https://www.sliderrevolution.com/design/cool-website-effects/) (article text + hero image URL; not Slider Revolution product or assets).

We **did not** use Slider Revolution, parallax page hijacking, video backgrounds, preloaders, or premium templates.

| Reference theme (article) | Our original implementation |
|---------------------------|---------------------------|
| Hero section animations | `hero.is-data-live` eyebrow pulse after real JSON load |
| SVG / line animations | Progressive **sparkline draw** from `cpih_yoy.json` / `psnb_monthly.json` |
| Scroll storytelling | **IntersectionObserver** `story-in-view` on insight cards (emphasis only) |
| Microinteractions | Button `:active` scale; chart filter **750ms** Chart.js update |
| Hover / card reveal | Touch-safe card `:active` on coarse pointers |

All metrics remain from committed pipeline JSON. Rollback before this pass: Worker `54f689cd`, `main` `c9361b3`.

## Editorial colour system (2026-11-07 brief)

Coordinated accent roles in `hub-tokens.css`: **teal** (fiscal / links), **cobalt** (section heads), **coral** (CPIH / warmth), **amber** (warm pills). Hero uses a light wash (not a dark wall) plus a **data stage** fed only from `computeMacroStory()`. Sparklines use gradient fills tied to `--hub-chart-cpih` / `--hub-chart-psnb`.
