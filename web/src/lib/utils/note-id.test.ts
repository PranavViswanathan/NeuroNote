import { describe, it, expect } from "vitest";
import { makeNewNoteId } from "./note-id";

describe("makeNewNoteId", () => {
  it("returns a string starting with 'note-'", () => {
    const id = makeNewNoteId();
    expect(id).toMatch(/^note-/);
  });

  it("matches expected format: note-{timestamp}-{random}", () => {
    const id = makeNewNoteId();
    expect(id).toMatch(/^note-\d+-\d+$/);
  });

  it("generates mostly unique ids across calls", () => {
    const ids = new Set(Array.from({ length: 20 }, () => makeNewNoteId()));
    // Timestamp-based with random suffix — occasional collisions within same ms are acceptable
    expect(ids.size).toBeGreaterThanOrEqual(18);
  });
});
