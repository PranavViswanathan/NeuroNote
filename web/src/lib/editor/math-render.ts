import katex from "katex";
import { normalizeMathLatex } from "./math";

export interface RenderMathResult {
  html: string;
  hasError: boolean;
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function renderMathToHtml(latex: string, displayMode: boolean): RenderMathResult {
  const normalized = normalizeMathLatex(latex);
  if (!normalized) {
    return { html: "", hasError: false };
  }

  try {
    return {
      html: katex.renderToString(normalized, {
        displayMode,
        throwOnError: true,
        strict: "warn",
      }),
      hasError: false,
    };
  } catch {
    const escaped = escapeHtml(normalized);
    const wrapped = displayMode ? `$$${escaped}$$` : `$${escaped}$`;
    return {
      html: `<span class=\"math-render-fallback\">${wrapped}</span>`,
      hasError: true,
    };
  }
}
