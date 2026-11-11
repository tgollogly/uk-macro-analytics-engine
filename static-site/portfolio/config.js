
// Hub preview: browser talks only to the public gate Worker (`uk-macro-ats-gate`); HMAC + private backend hold the model key.
// Original portfolio mirror: https://github.com/tgollogly/portfolio/blob/main/config.js
window.AI_BACKEND_URL =
  "https://uk-macro-ats-gate.thomasgolloglypagesdev.workers.dev/api";

window.CHAT_MAINTENANCE_MODE = true;
window.CHAT_MAINTENANCE_MESSAGE =
  "Chat is not bundled on this static hub. Open individual demos from the hub.";

window.CV_HIDDEN = true;
