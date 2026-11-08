# Host the portfolio on Vercel (free) + Streamlit (free)

## Why two places?

- **Vercel** serves **static HTML/CSS** fast — perfect for a **landing page** (`static-site/`).
- **Streamlit** is a **long-running Python process**. It does **not** run on standard Vercel serverless functions. Use **Streamlit Community Cloud** (free tier) for the live dashboard, or run locally for interviews.

## Deploy static landing (Vercel)

1. Push this repo to GitHub.
2. [vercel.com](https://vercel.com) → New Project → Import repo.
3. Set **Root Directory** to `static-site`.
4. Framework: **Other** (no build command). Output: `.` (default for static).
5. Deploy. You get `https://your-project.vercel.app`.

Edit `static-site/index.html` and add your **Streamlit Cloud app URL** as the main CTA when you have it.

## Deploy Streamlit app (free)

1. Push repo to GitHub.
2. [share.streamlit.io](https://share.streamlit.io) → New app → select repo, main file `streamlit_app.py`.
3. Python 3.11, `requirements.txt` for dependencies.
4. Copy the public Streamlit URL into `static-site/index.html` (and LinkedIn/application materials as needed — no public CV PDF on the hub).

## “Real-time” data

The dashboard **re-downloads ONS CSVs** when you click **Refresh data**. ONS updates on their release schedule — not a websocket feed.
