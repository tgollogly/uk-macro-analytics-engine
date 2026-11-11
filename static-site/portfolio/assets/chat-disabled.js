/**
 * Mirror stub: full chat widget (assets/chat.js from portfolio) is not bundled here.
 * It would call the AI backend; on this static hub we keep the Worker focused on assets only.
 */
(function () {
  "use strict";
  if (typeof window !== "undefined") {
    window.CHAT_MAINTENANCE_MODE = true;
    window.CHAT_MAINTENANCE_MESSAGE =
      "The AI assistant widget is not loaded on this demo hub. " +
      "Chat is not available on this static hub; use the project pages linked from the hub.";
  }
})();
