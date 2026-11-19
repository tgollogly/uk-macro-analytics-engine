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

/** Baseline headers for static HTML/assets (CSP left to Cloudflare dashboard if needed). */
function applyBaselineSecurityHeaders(headers) {
  headers.set("X-Content-Type-Options", "nosniff");
  headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  headers.set("X-Frame-Options", "SAMEORIGIN");
  headers.set(
    "Permissions-Policy",
    "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()",
  );
}

export default {
  async fetch(request, env) {
    const response = await env.ASSETS.fetch(request);
    const headers = new Headers(response.headers);
    if (response.status === 200) {
      applyBaselineSecurityHeaders(headers);
    }
    const policy = cacheControlFor(new URL(request.url));
    if (policy && response.status === 200) {
      headers.set("Cache-Control", policy);
    }
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  },
};
