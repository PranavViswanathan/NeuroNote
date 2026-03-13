export interface MathNodeAttributes {
  latex: string;
  displayMode: boolean;
}

export function normalizeMathLatex(latex: string): string {
  let normalized = latex.trim();
  if (normalized.startsWith("$$") && normalized.endsWith("$$") && normalized.length > 4) {
    normalized = normalized.slice(2, -2).trim();
  } else if (normalized.startsWith("$") && normalized.endsWith("$") && normalized.length > 2) {
    normalized = normalized.slice(1, -1).trim();
  }
  return normalized;
}

export function createInlineMathNode(latex: string): Record<string, unknown> {
  const normalized = normalizeMathLatex(latex);
  return {
    type: "mathInline",
    attrs: {
      latex: normalized,
      displayMode: false,
    },
  };
}

export function createBlockMathNode(latex: string): Record<string, unknown> {
  const normalized = normalizeMathLatex(latex);
  return {
    type: "mathBlock",
    attrs: {
      latex: normalized,
      displayMode: true,
    },
  };
}

export function getMathPlainTextFallback(latex: string, displayMode: boolean): string {
  const trimmed = latex.trim();
  if (!trimmed) {
    return "";
  }
  return displayMode ? `\n[math:${trimmed}]\n` : `[math:${trimmed}]`;
}
