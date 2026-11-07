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

export function drawSparkline(canvas, points, stroke, { yLabel = "" } = {}) {
  if (!canvas || !points.length) return;
  const ctx = canvas.getContext("2d");
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const w = canvas.clientWidth || 320;
  const h = canvas.clientHeight || 80;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, w, h);
  const ys = points.map((p) => p.y);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const pad = 4;
  const span = maxY - minY || 1;
  ctx.strokeStyle = stroke;
  ctx.lineWidth = 2;
  ctx.beginPath();
  points.forEach((p, i) => {
    const x = pad + (i / (points.length - 1 || 1)) * (w - pad * 2);
    const y = h - pad - ((p.y - minY) / span) * (h - pad * 2);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
  ctx.fillStyle = "#64748b";
  ctx.font = "11px system-ui,sans-serif";
  if (yLabel) ctx.fillText(yLabel, pad, 12);
}
