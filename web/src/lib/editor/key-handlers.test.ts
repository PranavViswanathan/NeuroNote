import { describe, expect, it } from "vitest";

import { resolveEditorKeydownAction } from "./key-handlers";

describe("resolveEditorKeydownAction", () => {
  it("opens command palette on cmd/ctrl+k", () => {
    expect(
      resolveEditorKeydownAction(
        { key: "k", ctrlKey: true },
        {
          disabled: false,
          hasSlashMenu: false,
          hasPalette: false,
          hasWikiMenu: false,
          hasBlockRefMenu: false,
        },
      ),
    ).toBe("open_palette");
  });

  it("executes slash selection on enter when slash menu is active", () => {
    expect(
      resolveEditorKeydownAction(
        { key: "Enter" },
        {
          disabled: false,
          hasSlashMenu: true,
          hasPalette: false,
          hasWikiMenu: false,
          hasBlockRefMenu: false,
        },
      ),
    ).toBe("slash_select");
  });

  it("executes wiki selection on enter when wiki menu is active", () => {
    expect(
      resolveEditorKeydownAction(
        { key: "Enter" },
        {
          disabled: false,
          hasSlashMenu: false,
          hasPalette: false,
          hasWikiMenu: true,
          hasBlockRefMenu: false,
        },
      ),
    ).toBe("wiki_select");
  });

  it("executes block-ref selection on enter when block-ref menu is active", () => {
    expect(
      resolveEditorKeydownAction(
        { key: "Enter" },
        {
          disabled: false,
          hasSlashMenu: false,
          hasPalette: false,
          hasWikiMenu: false,
          hasBlockRefMenu: true,
        },
      ),
    ).toBe("block_ref_select");
  });

  it("closes menus on escape", () => {
    expect(
      resolveEditorKeydownAction(
        { key: "Escape" },
        {
          disabled: false,
          hasSlashMenu: true,
          hasPalette: true,
          hasWikiMenu: true,
          hasBlockRefMenu: false,
        },
      ),
    ).toBe("close_menus");
  });

  it("returns none when editor is disabled", () => {
    expect(
      resolveEditorKeydownAction(
        { key: "Enter" },
        {
          disabled: true,
          hasSlashMenu: true,
          hasPalette: false,
          hasWikiMenu: false,
          hasBlockRefMenu: false,
        },
      ),
    ).toBe("none");
  });

  it("returns indent_block on Tab when nesting is valid", () => {
    expect(
      resolveEditorKeydownAction(
        { key: "Tab" },
        {
          disabled: false,
          hasSlashMenu: false,
          hasPalette: false,
          hasWikiMenu: false,
          hasBlockRefMenu: false,
          canIndentBlock: true,
          canOutdentBlock: false,
        },
      ),
    ).toBe("indent_block");
  });

  it("returns outdent_block on Shift+Tab when outdent is valid", () => {
    expect(
      resolveEditorKeydownAction(
        { key: "Tab", shiftKey: true },
        {
          disabled: false,
          hasSlashMenu: false,
          hasPalette: false,
          hasWikiMenu: false,
          hasBlockRefMenu: false,
          canIndentBlock: false,
          canOutdentBlock: true,
        },
      ),
    ).toBe("outdent_block");
  });
});
