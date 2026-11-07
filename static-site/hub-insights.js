/**
 * Deterministic macro insights from committed demo JSON (snapshot only).
 */

export function latestNonNullYoY(cpih) {
  for (let i = cpih.length - 1; i >= 0; i--) {
    const y = cpih[i]?.yoy_pct;
    if (y != null && Number.isFinite(y)) return { row: cpih[i], index: i };
  }
  return null;
}

export function yoyTwelveMonthsPrior(cpih, index) {
  let seen = 0;
  for (let i = index - 1; i >= 0; i--) {
    if (cpih[i]?.yoy_pct != null) {
      seen += 1;
      if (seen === 12) return cpih[i];
    }
  }
  return null;
}

export function latestPsnb(psnb) {
  if (!psnb.length) return null;
  return psnb[psnb.length - 1];
}

export function computeMacroStory(cpih, psnb, manifest) {
  const latestYoY = latestNonNullYoY(cpih);
  const priorYoY = latestYoY ? yoyTwelveMonthsPrior(cpih, latestYoY.index) : null;
  const psnbLast = latestPsnb(psnb);
  const asOf = manifest?.generated_at_utc ?? "unknown";
  const cpihRows = manifest?.sources?.cpih?.rows ?? cpih.length;
  const psnbRows = manifest?.sources?.psnb?.rows ?? psnb.length;

  let yoyDeltaPp = null;
  if (latestYoY && priorYoY && latestYoY.row.yoy_pct != null && priorYoY.yoy_pct != null) {
    yoyDeltaPp = Number((latestYoY.row.yoy_pct - priorYoY.yoy_pct).toFixed(2));
  }

  return {
    asOfUtc: asOf,
    cpihRows,
    psnbRows,
    cpih: latestYoY
      ? {
          month: latestYoY.row.obs_date.slice(0, 7),
          yoyPct: latestYoY.row.yoy_pct,
          priorMonth: priorYoY ? priorYoY.obs_date.slice(0, 7) : null,
          priorYoyPct: priorYoY?.yoy_pct ?? null,
          yoyDeltaPp,
        }
      : null,
    psnb: psnbLast
      ? {
          month: psnbLast.obs_date.slice(0, 7),
          gbpM: psnbLast.total_net_borrowing_gbp_m,
          rowCount: psnbLast.row_count ?? 1,
        }
      : null,
    limitations: manifest?.limitations ?? [],
  };
}

/** Last N non-null YoY points for sparkline (chronological). */
export function sparklineYoY(cpih, count = 36) {
  const pts = cpih.filter((r) => r.yoy_pct != null);
  return pts.slice(-count).map((r) => ({
    x: r.obs_date.slice(0, 7),
    y: r.yoy_pct,
  }));
}

export function sparklinePsnb(psnb, count = 36) {
  return psnb.slice(-count).map((r) => ({
    x: r.obs_date.slice(0, 7),
    y: r.total_net_borrowing_gbp_m,
  }));
}

function sparkGeometry(canvas, points) {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const w = canvas.clientWidth || 320;
  const h = canvas.clientHeight || 80;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  const ctx = canvas.getContext("2d");
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.scale(dpr, dpr);
  const ys = points.map((p) => p.y);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const pad = 4;
  const span = maxY - minY || 1;
  const coords = points.map((p, i) => ({
    x: pad + (i / (points.length - 1 || 1)) * (w - pad * 2),
    y: h - pad - ((p.y - minY) / span) * (h - pad * 2),
  }));
  return { ctx, w, h, pad, coords };
}

function paintSparkline(ctx, coords, stroke, progress, w, h, pad, yLabel, labelColor) {
  ctx.clearRect(0, 0, w, h);
  if (!coords.length) return;
  const last = Math.max(1, Math.ceil(coords.length * progress));
  const slice = coords.slice(0, last);
  const lastPt = slice[slice.length - 1];
  const baseY = h - pad;
  ctx.strokeStyle = "rgba(26, 35, 50, 0.08)";
  ctx.lineWidth = 1;
  for (let i = 1; i <= 3; i += 1) {
    const y = pad + ((h - pad * 2) * i) / 4;
    ctx.beginPath();
    ctx.moveTo(pad, y);
    ctx.lineTo(w - pad, y);
    ctx.stroke();
  }
  if (slice.length > 1) {
    ctx.beginPath();
    slice.forEach((c, i) => {
      if (i === 0) ctx.moveTo(c.x, c.y);
      else ctx.lineTo(c.x, c.y);
    });
    ctx.lineTo(lastPt.x, baseY);
    ctx.lineTo(slice[0].x, baseY);
    ctx.closePath();
    const grad = ctx.createLinearGradient(0, pad, 0, baseY);
    grad.addColorStop(0, stroke + "44");
    grad.addColorStop(1, stroke + "08");
    ctx.fillStyle = grad;
    ctx.fill();
  }
  ctx.strokeStyle = stroke;
  ctx.lineWidth = 2.25;
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  ctx.beginPath();
  slice.forEach((c, i) => {
    if (i === 0) ctx.moveTo(c.x, c.y);
    else ctx.lineTo(c.x, c.y);
  });
  ctx.stroke();
  if (progress >= 1 && lastPt) {
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(lastPt.x, lastPt.y, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = stroke;
    ctx.beginPath();
    ctx.arc(lastPt.x, lastPt.y, 3.25, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.fillStyle = labelColor || "#4a5568";
  ctx.font = "600 11px IBM Plex Mono, ui-monospace, monospace";
  if (yLabel) ctx.fillText(yLabel, pad, 13);
}

export function drawSparkline(canvas, points, stroke, { yLabel = "", animate = false, durationMs = 900 } = {}) {
  if (!canvas || !points.length) return;
  const reduced =
    typeof matchMedia !== "undefined" && matchMedia("(prefers-reduced-motion: reduce)").matches;
  const { ctx, w, h, pad, coords } = sparkGeometry(canvas, points);
  const doc = canvas.ownerDocument;
  const labelColor =
    doc?.defaultView
      ?.getComputedStyle(doc.documentElement)
      .getPropertyValue("--hub-text-secondary")
      .trim() || "#4a5568";
  if (!animate || reduced) {
    paintSparkline(ctx, coords, stroke, 1, w, h, pad, yLabel, labelColor);
    canvas.dataset.draw = "complete";
    return;
  }
  canvas.dataset.draw = "pending";
  const t0 = performance.now();
  const tick = (now) => {
    const p = Math.min(1, (now - t0) / durationMs);
    paintSparkline(ctx, coords, stroke, p, w, h, pad, yLabel, labelColor);
    if (p < 1) requestAnimationFrame(tick);
    else canvas.dataset.draw = "complete";
  };
  requestAnimationFrame(tick);
}
