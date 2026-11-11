/**
 * PROPOSED — points the hub ATS demo at the public GATE Worker (not the private backend).
 * Browser never holds ATS_INTERNAL_HMAC_SECRET or GEMINI_API_KEY.
 *
 * After deploy: substitute your account’s workers.dev subdomain from Cloudflare (Workers → uk-macro-ats-gate).
 * Shipped hub uses `config.js` with the same URL; this file remains as a documented template.
 */
window.AI_BACKEND_URL =
  "https://uk-macro-ats-gate.thomasgolloglypagesdev.workers.dev/api";

window.CHAT_MAINTENANCE_MODE = true;
window.CHAT_MAINTENANCE_MESSAGE =
  "Chat is not bundled on this static hub. Open individual demos from the hub.";

window.CV_HIDDEN = true;
