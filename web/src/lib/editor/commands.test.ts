import { describe, expect, it } from "vitest";

import {
  EDITOR_COMMANDS,
  filterEditorCommands,
  findSlashCommandMatch,
} from "./commands";

describe("EDITOR_COMMANDS", () => {
  it("covers required core block commands", () => {
    const ids = new Set(EDITOR_COMMANDS.map((command) => command.id));
    expect(ids).toEqual(
      new Set([
        "paragraph",
        "heading1",
        "heading2",
        "heading3",
        "bulletList",
        "orderedList",
        "checklist",
        "blockquote",
        "codeBlock",
        "divider",
      ]),
    );
  });
});

describe("filterEditorCommands", () => {
  it("returns all commands for an empty query", () => {
    expect(filterEditorCommands("")).toEqual(EDITOR_COMMANDS);
  });

  it("filters by label and keyword, case-insensitive", () => {
    expect(filterEditorCommands("h1").map((item) => item.id)).toContain("heading1");
    expect(filterEditorCommands("quote").map((item) => item.id)).toContain("blockquote");
  });

  it("returns an empty array for unknown query", () => {
    expect(filterEditorCommands("this-does-not-exist")).toEqual([]);
  });
});

describe("findSlashCommandMatch", () => {
  it("detects slash command query at the end of block text", () => {
    expect(findSlashCommandMatch("/h1", 5)).toEqual({
      from: 5,
      to: 8,
      query: "h1",
    });
  });

  it("supports command trigger after whitespace", () => {
    expect(findSlashCommandMatch("Write /code", 10)).toEqual({
      from: 16,
      to: 21,
      query: "code",
    });
  });

  it("returns null when cursor is not inside an active slash command", () => {
    expect(findSlashCommandMatch("Write /code here", 10)).toBeNull();
    expect(findSlashCommandMatch("normal text", 10)).toBeNull();
  });
});
