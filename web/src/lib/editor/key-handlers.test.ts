import { describe, expect, it } from "vitest";

import { resolveEditorKeydownAction } from "./key-handlers";

describe("resolveEditorKeydownAction", () => {
  it("opens command palette on cmd/ctrl+k", () => {
    expect(
      resolveEditorKeydownAction(
        { key: "k", ctrlKey: true },
        { disabled: false, hasSlashMenu: false, hasPalette: false, hasWikiMenu: false },
      ),
    ).toBe("open_palette");
  });

  it("executes slash selection on enter when slash menu is active", () => {
    expect(
      resolveEditorKeydownAction(
        { key: "Enter" },
        { disabled: false, hasSlashMenu: true, hasPalette: false, hasWikiMenu: false },
      ),
    ).toBe("slash_select");
  });

  it("executes wiki selection on enter when wiki menu is active", () => {
    expect(
      resolveEditorKeydownAction(
        { key: "Enter" },
        { disabled: false, hasSlashMenu: false, hasPalette: false, hasWikiMenu: true },
      ),
    ).toBe("wiki_select");
  });

  it("closes menus on escape", () => {
    expect(
      resolveEditorKeydownAction(
        { key: "Escape" },
        { disabled: false, hasSlashMenu: true, hasPalette: true, hasWikiMenu: true },
      ),
    ).toBe("close_menus");
  });

  it("returns none when editor is disabled", () => {
    expect(
      resolveEditorKeydownAction(
        { key: "Enter" },
        { disabled: true, hasSlashMenu: true, hasPalette: false, hasWikiMenu: false },
      ),
    ).toBe("none");
  });
});
