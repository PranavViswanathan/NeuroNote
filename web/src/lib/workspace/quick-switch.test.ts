import { describe, expect, it } from "vitest";

import {
  buildQuickSwitchItems,
  filterQuickSwitchItems,
  type BuildQuickSwitchItemsInput,
} from "./quick-switch";

function buildInput(overrides?: Partial<BuildQuickSwitchItemsInput>): BuildQuickSwitchItemsInput {
  return {
    selectedNoteId: "note-a",
    notes: [
      {
        note_id: "note-a",
        note_title: "Alpha Note",
        subject_id: "inbox",
        tags: ["alpha"],
        is_pinned: false,
        is_archived: false,
        content_text: "Alpha content",
        updated_at: "2026-03-13T10:00:00Z",
        version: 1,
      },
      {
        note_id: "note-b",
        note_title: "Beta Note",
        subject_id: "research",
        tags: ["beta"],
        is_pinned: true,
        is_archived: false,
        content_text: "Beta content",
        updated_at: "2026-03-13T10:01:00Z",
        version: 1,
      },
    ],
    ...overrides,
  };
}

describe("quick-switch helpers", () => {
  it("builds action and note items", () => {
    const items = buildQuickSwitchItems(buildInput());
    const titles = items.map((item) => item.title);

    expect(titles).toContain("Create note");
    expect(titles).toContain("Pin selected note");
    expect(titles).toContain("Archive selected note");
    expect(titles).toContain("Alpha Note");
    expect(titles).toContain("Beta Note");
  });

  it("switches selected actions based on selected note state", () => {
    const items = buildQuickSwitchItems(buildInput({ selectedNoteId: "note-b" }));
    const titles = items.map((item) => item.title);

    expect(titles).toContain("Unpin selected note");
    expect(titles).toContain("Archive selected note");
  });

  it("filters by title, subtitle, and keywords", () => {
    const items = buildQuickSwitchItems(buildInput());
    expect(filterQuickSwitchItems({ items, query: "research" }).map((item) => item.title)).toEqual(["Beta Note"]);
    expect(filterQuickSwitchItems({ items, query: "create" }).map((item) => item.title)).toEqual(["Create note"]);
    expect(filterQuickSwitchItems({ items, query: "alpha" }).map((item) => item.title)).toContain("Alpha Note");
  });
});
