import { h } from "../dom.js";
import { drawOverlay } from "../overlay.js";

/**
 * The photo with OpenCV's marks, plus the agent's one-line instruction.
 * @param {string} photoUrl
 * @param {any|null} result
 * @param {string} line
 * @param {string} tone
 */
export function photoPanel(photoUrl, result, line, tone = "info") {
  const img = /** @type {HTMLImageElement} */ (h("img", { class: "result-photo", src: photoUrl, alt: "Meter ki photo" }));
  const canvas = /** @type {HTMLCanvasElement} */ (h("canvas", { class: "result-overlay", "aria-hidden": "true" }));
  const strip = h("p", { class: `agent-strip ${tone}`, role: "status" }, line);
  const panel = h("div", { class: "photo-panel" }, h("div", { class: "photo-frame" }, img, canvas), strip);
  const redraw = (override) => {
    if (result && img.complete && img.naturalWidth) drawOverlay(canvas, img, result, override);
  };
  img.addEventListener("load", () => redraw());
  window.addEventListener("resize", () => redraw(), { passive: true });
  return {
    panel,
    redraw,
    /** @param {string} text @param {string} [nextTone] */
    say(text, nextTone) {
      strip.textContent = text;
      if (nextTone) strip.className = `agent-strip ${nextTone}`;
    },
  };
}

/** @param {string} label @param {() => void} run @param {string} [variant] */
export function actionBar(label, run, variant = "") {
  return h("div", { class: "action-bar" }, h("button", { class: `button ${variant}`, onClick: run }, label));
}
