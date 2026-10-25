const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

/**
 * @param {CanvasRenderingContext2D} ctx
 * @param {number[][]} quad
 * @param {number} scale
 */
function tracePath(ctx, quad, scale) {
  ctx.beginPath();
  quad.forEach(([x, y], i) => (i ? ctx.lineTo(x * scale, y * scale) : ctx.moveTo(x * scale, y * scale)));
  ctx.closePath();
}

/**
 * Draws glare marks, the serial box and one box per digit with its confidence.
 * @param {HTMLCanvasElement} canvas
 * @param {HTMLImageElement} img
 * @param {any} result
 * @param {{confidences?: number[], unclear?: number[]}} [override]
 */
export function drawOverlay(canvas, img, result, override = {}) {
  const width = img.clientWidth;
  const height = img.clientHeight;
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.round(width * ratio);
  canvas.height = Math.round(height * ratio);
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, width, height);
  const scale = width / result.image.width;
  const line = Math.max(2, width / 180);
  const problem = css("--problem") || "#d92d20";
  const good = "#22c55e";
  const unsure = "#facc15";

  for (const mark of result.marks ?? []) {
    const [x0, y0, x1, y1] = mark.box.map((v) => v * scale);
    ctx.fillStyle = "rgba(217, 45, 32, 0.25)";
    ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
    ctx.strokeStyle = problem;
    ctx.lineWidth = line;
    ctx.strokeRect(x0, y0, x1 - x0, y1 - y0);
  }

  if (result.serial) {
    const ok = result.serial.status === "match" || result.serial.status === "read";
    tracePath(ctx, result.serial.quad, scale);
    ctx.strokeStyle = ok ? good : problem;
    ctx.lineWidth = line;
    ctx.stroke();
  }

  const display = result.display;
  if (!display) return;
  const confidences = override.confidences ?? display.confidences;
  const unclear = new Set(override.unclear ?? display.unclear_positions);
  ctx.textAlign = "center";
  display.digit_quads.forEach((quad, i) => {
    const boxWidth = Math.abs(quad[1][0] - quad[0][0]) * scale;
    const size = Math.max(9, Math.min(18, Math.round(boxWidth * 0.42)));
    ctx.font = `600 ${size}px "Plex Mono", monospace`;
    const color = unclear.has(i) ? unsure : good;
    tracePath(ctx, quad, scale);
    ctx.strokeStyle = color;
    ctx.lineWidth = line;
    ctx.stroke();
    const cx = ((quad[0][0] + quad[1][0]) / 2) * scale;
    const top = Math.min(quad[0][1], quad[1][1]) * scale - 6;
    const label = `${Math.min(99, Math.round((confidences[i] ?? 0) * 100))}`;
    ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
    const w = ctx.measureText(label).width + 8;
    ctx.fillRect(cx - w / 2, top - size, w, size + 4);
    ctx.fillStyle = color;
    ctx.fillText(label, cx, top);
  });
}
