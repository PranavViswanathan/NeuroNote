import { describe, expect, it } from "vitest";

import {
  createBlockMathNode,
  createInlineMathNode,
  getMathPlainTextFallback,
  normalizeMathLatex,
} from "./math";

describe("math helpers", () => {
  it("creates inline and block math nodes", () => {
    expect(createInlineMathNode("mc^2")).toEqual({
      type: "mathInline",
      attrs: { latex: "mc^2", displayMode: false },
    });
    expect(createBlockMathNode("x^2")).toEqual({
      type: "mathBlock",
      attrs: { latex: "x^2", displayMode: true },
    });
  });

  it("returns deterministic plain text fallback", () => {
    expect(getMathPlainTextFallback("x+y", false)).toBe("[math:x+y]");
    expect(getMathPlainTextFallback("x+y", true)).toBe("\n[math:x+y]\n");
  });

  it("normalizes wrapped latex input", () => {
    expect(normalizeMathLatex("  $x^2+y^2$ ")).toBe("x^2+y^2");
    expect(normalizeMathLatex("$$\\int_0^1 x \\\\, dx$$")).toBe("\\int_0^1 x \\\\, dx");
    expect(normalizeMathLatex("x^2+y^2")).toBe("x^2+y^2");
  });
});
