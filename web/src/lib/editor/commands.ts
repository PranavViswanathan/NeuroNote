export type EditorCommandId =
  | "paragraph"
  | "heading1"
  | "heading2"
  | "heading3"
  | "bulletList"
  | "orderedList"
  | "checklist"
  | "blockquote"
  | "codeBlock"
  | "divider";

export interface EditorCommandDefinition {
  id: EditorCommandId;
  label: string;
  keywords: string[];
}

export interface SlashCommandMatch {
  from: number;
  to: number;
  query: string;
}

export const EDITOR_COMMANDS: EditorCommandDefinition[] = [
  { id: "paragraph", label: "Paragraph", keywords: ["text", "body", "p"] },
  { id: "heading1", label: "H1", keywords: ["heading", "title", "h1"] },
  { id: "heading2", label: "H2", keywords: ["heading", "subtitle", "h2"] },
  { id: "heading3", label: "H3", keywords: ["heading", "section", "h3"] },
  { id: "bulletList", label: "Bullet List", keywords: ["list", "bullet", "ul"] },
  { id: "orderedList", label: "Numbered List", keywords: ["list", "ordered", "ol"] },
  { id: "checklist", label: "Checklist", keywords: ["task", "todo", "check"] },
  { id: "blockquote", label: "Quote", keywords: ["quote", "blockquote", "callout"] },
  { id: "codeBlock", label: "Code Block", keywords: ["code", "snippet", "pre"] },
  { id: "divider", label: "Divider", keywords: ["divider", "rule", "line"] },
];

export function filterEditorCommands(query: string): EditorCommandDefinition[] {
  const normalized = query.trim().toLowerCase();
  if (!normalized) {
    return EDITOR_COMMANDS;
  }
  return EDITOR_COMMANDS.filter((command) => {
    if (command.label.toLowerCase().includes(normalized)) {
      return true;
    }
    return command.keywords.some((keyword) => keyword.toLowerCase().includes(normalized));
  });
}

export function findSlashCommandMatch(textBeforeCursor: string, blockStartPos: number): SlashCommandMatch | null {
  const match = /(?:^|\s)\/([a-z0-9-]*)$/i.exec(textBeforeCursor);
  if (!match) {
    return null;
  }
  const fullMatch = match[0];
  const slashOffset = match.index + fullMatch.lastIndexOf("/");
  return {
    from: blockStartPos + slashOffset,
    to: blockStartPos + textBeforeCursor.length,
    query: match[1] ?? "",
  };
}
