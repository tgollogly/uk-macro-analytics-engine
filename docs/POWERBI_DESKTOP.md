# Power BI Desktop (free) — use this repo’s CSV exports

[Power BI Desktop](https://powerbi.microsoft.com/desktop/) is free to install. It is a credible way to show **data visualisation** and **stakeholder-ready** outputs without paying for a service.

## Steps

1. Run the pipeline so exports exist:

   ```bash
   python -m src.analytics
   ```

2. Open Power BI Desktop → **Get data** → **Text/CSV**.

3. Load:

   - `data/exports/cpih_yoy.csv` — line chart: `obs_date` on axis, `yoy_pct` as value.
   - `data/exports/psnb_monthly.csv` — column or line: `obs_date`, `total_net_borrowing_gbp_m`.

4. Add a **slicer** for date range and a **card** for latest YoY %.

5. Save as `.pbix` locally. For GitHub, export a **PNG** of the report page and add it to `tools/source/hero.png` or a `docs/screenshots/` folder (optional).

## Licensing

Power BI Desktop is free; publishing to Power BI Service may require a work or trial account. For a portfolio, **screenshots** + **PBIX in releases** (optional) are often enough.
