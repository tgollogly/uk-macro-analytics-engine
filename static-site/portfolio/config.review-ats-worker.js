/**
 * PROPOSED (review only — do not rename to config.js until user approves deploy).
 * After Worker `uk-macro-ats-api` is live and bearer token + origins are set:
 *   window.AI_BACKEND_URL = "https://uk-macro-ats-api.<subdomain>.workers.dev/api";
 * Add header from the static page is NOT possible with fetch alone; either:
 *   - use a Workers route + same-origin proxy, or
 *   - deploy with ATS_ALLOWED_ORIGINS only (no bearer), accepting residual abuse risk until hardened.
 *
 * Current production hub still uses ./config.js → https://tgollogly.dev/api
 */
window.AI_BACKEND_URL = ""; // set to deployed Worker URL after approval

window.CHAT_MAINTENANCE_MODE = true;
window.CHAT_MAINTENANCE_MESSAGE =
  "Chat is not bundled on this static hub. Use the portfolio site or open individual demos from the hub.";

window.CV_HIDDEN = true;
