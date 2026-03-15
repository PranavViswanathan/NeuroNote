import { describe, expect, it } from "vitest";

import { findBlockRefMatch, normalizeBlockRefToken, toBlockRefToken } from "./block-refs";

describe("block refs", () => {
  it("detects an open block-ref query before cursor", () => {
    const match = findBlockRefMatch("Link to ((demo-block", 100);
    expect(match).toEqual({
      from: 108,
      to: 120,
      query: "demo-block",
    });
  });

  it("returns null when block-ref is already closed", () => {
    expect(findBlockRefMatch("Already ((done)) token", 0)).toBeNull();
  });

  it("normalizes wrapped block-ref token", () => {
    expect(normalizeBlockRefToken("((abc-123))")).toBe("abc-123");
  });

  it("builds canonical block-ref token format", () => {
    expect(toBlockRefToken(" abc-123 ")).toBe("((abc-123))");
  });
});
