/**
 * Minimal Worker: serve static assets from static-site/ (HTML, CSS, images).
 * No secrets. Add routes or HTMLRewriter here only when needed.
 */
export default {
  async fetch(request, env) {
    return env.ASSETS.fetch(request);
  },
};
