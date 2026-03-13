import { describe, expect, it } from "vitest";

import { findWikiLinkMatch, normalizeWikiLinkTitle } from "./wiki-links";

describe("findWikiLinkMatch", () => {
  it("detects an open wiki-link query before cursor", () => {
    expect(findWikiLinkMatch("See [[Graph", 4)).toEqual({
      from: 8,
      to: 15,
      query: "Graph",
    });
  });

  it("supports an empty query right after [[", () => {
    expect(findWikiLinkMatch("[[", 20)).toEqual({
      from: 20,
      to: 22,
      query: "",
    });
  });

  it("returns null when wiki-link is already closed", () => {
    expect(findWikiLinkMatch("See [[Graph]]", 4)).toBeNull();
  });
});

describe("normalizeWikiLinkTitle", () => {
  it("trims and collapses interior whitespace", () => {
    expect(normalizeWikiLinkTitle("  Graph   Reasoning  Notes  ")).toBe("Graph Reasoning Notes");
  });

  it("removes wrapping brackets if present", () => {
    expect(normalizeWikiLinkTitle("[[Neuro Note]]")).toBe("Neuro Note");
  });
});
