# Streamlit portfolio dashboard (free, local)

Interactive KPIs, Plotly charts, tabs, and CSV downloads over the same pipeline as the CLI.

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

- **Refresh data** in the sidebar forces a **new ONS download** (then caches in `data/cache/parquet/`).
- **Live data** here means “whatever ONS serves today at their public CSV URL” — not a websocket or sub-second market feed.

### Optional: Streamlit Community Cloud (free tier)

Push the repo to GitHub, then [share.streamlit.io](https://share.streamlit.io) can run `streamlit_app.py`. You still need compliance with ONS attribution (footer text is in the app).
