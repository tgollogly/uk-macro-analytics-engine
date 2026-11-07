/**
 * Serve static-site/ via ASSETS and set cache policy so HTML revalidates while
 * versioned (?v=) CSS/JS can cache immutably. No service worker on this site.
 */
function cacheControlFor(url) {
  const path = url.pathname;
  const hasVersion = url.searchParams.has("v");
  if (hasVersion && /\.(css|js|mjs)$/i.test(path)) {
    return "public, max-age=31536000, immutable";
  }
  const isHtml =
    path === "/" ||
    path.endsWith(".html") ||
    (!path.includes(".") && !path.endsWith("/"));
  if (isHtml || path.endsWith("/index.html")) {
    return "public, max-age=0, must-revalidate";
  }
  if (/\.(css|js|mjs)$/i.test(path)) {
    return "public, max-age=0, must-revalidate";
  }
  if (/\.(png|jpg|jpeg|gif|webp|svg|ico|woff2?)$/i.test(path)) {
    return "public, max-age=86400, must-revalidate";
  }
  return null;
}

export default {
  async fetch(request, env) {
    const response = await env.ASSETS.fetch(request);
    const policy = cacheControlFor(new URL(request.url));
    if (!policy || response.status !== 200) {
      return response;
    }
    const headers = new Headers(response.headers);
    headers.set("Cache-Control", policy);
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  },
};
