export interface EditorHotkeyEvent {
  key: string;
  metaKey?: boolean;
  ctrlKey?: boolean;
  shiftKey?: boolean;
}

export interface EditorKeydownContext {
  disabled: boolean;
  hasSlashMenu: boolean;
  hasPalette: boolean;
  hasWikiMenu: boolean;
  hasBlockRefMenu?: boolean;
  canIndentBlock?: boolean;
  canOutdentBlock?: boolean;
}

export type EditorKeydownAction =
  | "none"
  | "open_palette"
  | "close_menus"
  | "slash_select"
  | "wiki_select"
  | "block_ref_select"
  | "move_next"
  | "move_prev"
  | "indent_block"
  | "outdent_block";

export function resolveEditorKeydownAction(
  event: EditorHotkeyEvent,
  context: EditorKeydownContext,
): EditorKeydownAction {
  if (context.disabled) {
    return "none";
  }

  const isMetaK = (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k";
  if (isMetaK) {
    return "open_palette";
  }

  if (event.key === "Escape") {
    if (context.hasPalette || context.hasSlashMenu || context.hasWikiMenu || context.hasBlockRefMenu) {
      return "close_menus";
    }
    return "none";
  }

  if (event.key === "ArrowDown") {
    if (context.hasWikiMenu || context.hasBlockRefMenu || context.hasPalette || context.hasSlashMenu) {
      return "move_next";
    }
    return "none";
  }

  if (event.key === "ArrowUp") {
    if (context.hasWikiMenu || context.hasBlockRefMenu || context.hasPalette || context.hasSlashMenu) {
      return "move_prev";
    }
    return "none";
  }

  if (event.key === "Enter") {
    if (context.hasBlockRefMenu) {
      return "block_ref_select";
    }
    if (context.hasWikiMenu) {
      return "wiki_select";
    }
    if (context.hasPalette || context.hasSlashMenu) {
      return "slash_select";
    }
    return "none";
  }

  if (
    event.key === "Tab"
    && !context.hasPalette
    && !context.hasSlashMenu
    && !context.hasWikiMenu
    && !context.hasBlockRefMenu
  ) {
    if (event.shiftKey) {
      return context.canOutdentBlock ? "outdent_block" : "none";
    }
    return context.canIndentBlock ? "indent_block" : "none";
  }

  return "none";
}
