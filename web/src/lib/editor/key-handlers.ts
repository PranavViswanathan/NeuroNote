export interface EditorHotkeyEvent {
  key: string;
  metaKey?: boolean;
  ctrlKey?: boolean;
}

export interface EditorKeydownContext {
  disabled: boolean;
  hasSlashMenu: boolean;
  hasPalette: boolean;
  hasWikiMenu: boolean;
}

export type EditorKeydownAction =
  | "none"
  | "open_palette"
  | "close_menus"
  | "slash_select"
  | "wiki_select"
  | "move_next"
  | "move_prev";

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
    if (context.hasPalette || context.hasSlashMenu || context.hasWikiMenu) {
      return "close_menus";
    }
    return "none";
  }

  if (event.key === "ArrowDown") {
    if (context.hasWikiMenu || context.hasPalette || context.hasSlashMenu) {
      return "move_next";
    }
    return "none";
  }

  if (event.key === "ArrowUp") {
    if (context.hasWikiMenu || context.hasPalette || context.hasSlashMenu) {
      return "move_prev";
    }
    return "none";
  }

  if (event.key === "Enter") {
    if (context.hasWikiMenu) {
      return "wiki_select";
    }
    if (context.hasPalette || context.hasSlashMenu) {
      return "slash_select";
    }
    return "none";
  }

  return "none";
}
