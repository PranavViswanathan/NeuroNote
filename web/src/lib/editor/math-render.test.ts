import { describe, expect, it } from "vitest";

import { renderMathToHtml } from "./math-render";

describe("renderMathToHtml", () => {
  it("renders valid latex as katex html", () => {
    const result = renderMathToHtml("x^2+y^2", false);
    expect(result.hasError).toBe(false);
    expect(result.html).toContain("katex");
    expect(result.html).not.toContain("$x^2+y^2$");
  });

  it("renders wrapped delimiters as valid math", () => {
    const result = renderMathToHtml("$x^2+y^2$", false);
    expect(result.hasError).toBe(false);
    expect(result.html).toContain("katex");
    expect(result.html).not.toContain("math-render-fallback");
  });

  it("falls back for invalid latex", () => {
    const result = renderMathToHtml("\\frac{1}{", true);
    expect(result.hasError).toBe(true);
    expect(result.html).toContain("math-render-fallback");
  });
});
