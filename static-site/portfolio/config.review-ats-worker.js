/**
 * PROPOSED — points the hub ATS demo at the public GATE Worker (not the private backend).
 * Browser never holds ATS_INTERNAL_HMAC_SECRET or GEMINI_API_KEY.
 *
 * After deploy: substitute your account’s workers.dev subdomain from Cloudflare (Workers → uk-macro-ats-gate).
 * Do NOT rename this file to config.js until user approves — keeps current hub on tgollogly.dev/api.
 */
window.AI_BACKEND_URL =
  "https://uk-macro-ats-gate.<YOUR_ACCOUNT_SUBDOMAIN>.workers.dev/api";

window.CHAT_MAINTENANCE_MODE = true;
window.CHAT_MAINTENANCE_MESSAGE =
  "Chat is not bundled on this static hub. Use the portfolio site or open individual demos from the hub.";

window.CV_HIDDEN = true;
