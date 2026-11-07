/**
 * WCAG 2.1 contrast from computed CSS colours (sRGB, 8-bit).
 */

export function parseCssRgb(css) {
  if (!css || css === "transparent") return null;
  const m = css.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (m) return [Number(m[1]), Number(m[2]), Number(m[3])];
  if (css.startsWith("#")) {
    const h = css.slice(1);
    if (h.length === 3) {
      return [parseInt(h[0] + h[0], 16), parseInt(h[1] + h[1], 16), parseInt(h[2] + h[2], 16)];
    }
    if (h.length === 6) {
      return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
    }
  }
  return null;
}

function lin(c) {
  const x = c / 255;
  return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4;
}

export function relLuminance([r, g, b]) {
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}

export function contrastRatio(fgRgb, bgRgb) {
  const l1 = relLuminance(fgRgb);
  const l2 = relLuminance(bgRgb);
  const hi = Math.max(l1, l2);
  const lo = Math.min(l1, l2);
  return (hi + 0.05) / (lo + 0.05);
}

/** Best-effort opaque background for an element (walk up). */
export function effectiveBackgroundRgb(node) {
  let el = node;
  while (el && el !== document.documentElement) {
    const cs = getComputedStyle(el);
    const rgb = parseCssRgb(cs.backgroundColor);
    if (rgb && cs.backgroundColor !== "rgba(0, 0, 0, 0)") return rgb;
    el = el.parentElement;
  }
  const body = parseCssRgb(getComputedStyle(document.body).backgroundColor);
  return body || [250, 248, 244];
}

export function measureElementContrast(el) {
  const cs = getComputedStyle(el);
  const fg = parseCssRgb(cs.color);
  const webkit = parseCssRgb(cs.webkitTextFillColor);
  const fill = webkit && cs.webkitTextFillColor !== "rgba(0, 0, 0, 0)" ? webkit : fg;
  const bg = effectiveBackgroundRgb(el);
  if (!fill || !bg) return { ok: false, reason: "unparsed", color: cs.color, webkit: cs.webkitTextFillColor };
  const ratio = contrastRatio(fill, bg);
  return {
    ok: true,
    ratio,
    color: cs.color,
    webkitTextFill: cs.webkitTextFillColor,
    bgRgb: bg,
    fontSize: cs.fontSize,
    fontWeight: cs.fontWeight,
  };
}
