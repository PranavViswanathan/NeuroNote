"use client";

import { EditorContent, useEditor, type JSONContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  EDITOR_COMMANDS,
  filterEditorCommands,
  findSlashCommandMatch,
  type EditorCommandDefinition,
  type EditorCommandId,
  type SlashCommandMatch,
} from "../../lib/editor/commands";
import { resolveEditorKeydownAction } from "../../lib/editor/key-handlers";
import { findWikiLinkMatch, normalizeWikiLinkTitle, type WikiLinkMatch } from "../../lib/editor/wiki-links";

export interface TipTapUpdatePayload {
  json: JSONContent;
  text: string;
}

export interface WikiLinkSuggestion {
  noteId: string;
  title: string;
}

interface TipTapEditorProps {
  value: JSONContent;
  onUpdate: (payload: TipTapUpdatePayload) => void;
  onBlur: () => void;
  disabled?: boolean;
  onSearchWikiLinks?: (query: string) => Promise<WikiLinkSuggestion[]>;
  onCreateWikiLink?: (title: string) => Promise<WikiLinkSuggestion>;
  onEditorError?: (message: string) => void;
}

type WikiMenuOption =
  | {
      kind: "existing";
      title: string;
      noteId: string;
    }
  | {
      kind: "create";
      title: string;
    };

const MAX_COMMAND_ITEMS = 8;

function clampIndex(index: number, size: number): number {
  if (size <= 0) {
    return 0;
  }
  if (index < 0) {
    return size - 1;
  }
  if (index >= size) {
    return 0;
  }
  return index;
}

interface KeyboardEventLike {
  key: string;
  metaKey: boolean;
  ctrlKey: boolean;
  preventDefault: () => void;
}

export function TipTapEditor({
  value,
  onUpdate,
  onBlur,
  disabled = false,
  onSearchWikiLinks,
  onCreateWikiLink,
  onEditorError,
}: TipTapEditorProps) {
  const serializedValue = JSON.stringify(value);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [paletteQuery, setPaletteQuery] = useState("");
  const [paletteSelectedIndex, setPaletteSelectedIndex] = useState(0);
  const [slashMatch, setSlashMatch] = useState<SlashCommandMatch | null>(null);
  const [slashQuery, setSlashQuery] = useState("");
  const [slashSelectedIndex, setSlashSelectedIndex] = useState(0);
  const [wikiMatch, setWikiMatch] = useState<WikiLinkMatch | null>(null);
  const [wikiSuggestions, setWikiSuggestions] = useState<WikiLinkSuggestion[]>([]);
  const [wikiSelectedIndex, setWikiSelectedIndex] = useState(0);
  const [wikiLoading, setWikiLoading] = useState(false);
  const wikiSearchTokenRef = useRef(0);
  const keydownHandlerRef = useRef<(event: KeyboardEventLike) => boolean>(() => false);

  const resolveInlineMenus = useCallback(
    (editorTextBeforeCursor: string, blockStartPos: number) => {
      const nextSlashMatch = findSlashCommandMatch(editorTextBeforeCursor, blockStartPos);
      if (nextSlashMatch) {
        setSlashMatch(nextSlashMatch);
        setSlashQuery(nextSlashMatch.query);
        setSlashSelectedIndex(0);
      } else {
        setSlashMatch(null);
        setSlashQuery("");
      }

      if (!onSearchWikiLinks) {
        setWikiMatch(null);
        return;
      }

      const nextWikiMatch = findWikiLinkMatch(editorTextBeforeCursor, blockStartPos);
      setWikiMatch(nextWikiMatch);
      if (!nextWikiMatch) {
        setWikiSuggestions([]);
      }
    },
    [onSearchWikiLinks],
  );

  const editor = useEditor({
    extensions: [StarterKit],
    content: value,
    editable: !disabled,
    onUpdate: ({ editor: tiptapEditor }) => {
      const { $from } = tiptapEditor.state.selection;
      const blockText = $from.parent.textContent.slice(0, $from.parentOffset);
      resolveInlineMenus(blockText, $from.start());

      onUpdate({
        json: tiptapEditor.getJSON(),
        text: tiptapEditor.getText(),
      });
    },
    onBlur: () => {
      onBlur();
    },
    onSelectionUpdate: ({ editor: tiptapEditor }) => {
      const { $from } = tiptapEditor.state.selection;
      const blockText = $from.parent.textContent.slice(0, $from.parentOffset);
      resolveInlineMenus(blockText, $from.start());
    },
    editorProps: {
      handleKeyDown: (_view, event) => keydownHandlerRef.current(event),
    },
  });

  const commandItems = useMemo<EditorCommandDefinition[]>(() => {
    if (paletteOpen) {
      return filterEditorCommands(paletteQuery).slice(0, MAX_COMMAND_ITEMS);
    }
    if (slashMatch) {
      return filterEditorCommands(slashQuery).slice(0, MAX_COMMAND_ITEMS);
    }
    return [];
  }, [paletteOpen, paletteQuery, slashMatch, slashQuery]);

  const wikiOptions = useMemo<WikiMenuOption[]>(() => {
    if (!wikiMatch) {
      return [];
    }

    const options: WikiMenuOption[] = wikiSuggestions.map((suggestion) => ({
      kind: "existing",
      noteId: suggestion.noteId,
      title: suggestion.title,
    }));

    const normalizedQuery = normalizeWikiLinkTitle(wikiMatch.query);
    if (!normalizedQuery) {
      return options;
    }

    const hasExact = options.some(
      (option) => option.title.toLowerCase() === normalizedQuery.toLowerCase(),
    );
    if (!hasExact) {
      options.push({ kind: "create", title: normalizedQuery });
    }

    return options;
  }, [wikiMatch, wikiSuggestions]);

  useEffect(() => {
    if (!editor) {
      return;
    }
    const currentSerialized = JSON.stringify(editor.getJSON());
    if (currentSerialized === serializedValue) {
      return;
    }
    editor.commands.setContent(value, false);
  }, [editor, value, serializedValue]);

  useEffect(() => {
    if (!editor) {
      return;
    }
    editor.setEditable(!disabled);
  }, [disabled, editor]);

  useEffect(() => {
    if (!wikiMatch || !onSearchWikiLinks) {
      return;
    }

    const token = wikiSearchTokenRef.current + 1;
    wikiSearchTokenRef.current = token;
    setWikiLoading(true);

    void onSearchWikiLinks(wikiMatch.query)
      .then((results) => {
        if (wikiSearchTokenRef.current !== token) {
          return;
        }
        setWikiSuggestions(results);
        setWikiSelectedIndex(0);
      })
      .catch(() => {
        if (wikiSearchTokenRef.current !== token) {
          return;
        }
        setWikiSuggestions([]);
      })
      .finally(() => {
        if (wikiSearchTokenRef.current === token) {
          setWikiLoading(false);
        }
      });
  }, [onSearchWikiLinks, wikiMatch]);

  const runCommand = useCallback(
    (commandId: EditorCommandId, deleteMatch?: { from: number; to: number }) => {
      if (!editor) {
        return;
      }

      let chain = editor.chain().focus();
      if (deleteMatch) {
        chain = chain.deleteRange(deleteMatch);
      }

      switch (commandId) {
        case "paragraph":
          chain = chain.setParagraph();
          break;
        case "heading1":
          chain = chain.toggleHeading({ level: 1 });
          break;
        case "heading2":
          chain = chain.toggleHeading({ level: 2 });
          break;
        case "heading3":
          chain = chain.toggleHeading({ level: 3 });
          break;
        case "bulletList":
          chain = chain.toggleBulletList();
          break;
        case "orderedList":
          chain = chain.toggleOrderedList();
          break;
        case "checklist":
          chain = chain.toggleBulletList();
          break;
        case "blockquote":
          chain = chain.toggleBlockquote();
          break;
        case "codeBlock":
          chain = chain.toggleCodeBlock();
          break;
        case "divider":
          chain = chain.setHorizontalRule();
          break;
        default:
          break;
      }

      chain.run();
      setSlashMatch(null);
      setSlashQuery("");
      setPaletteOpen(false);
      setPaletteQuery("");
    },
    [editor],
  );

  const applyWikiLink = useCallback(
    async (option: WikiMenuOption) => {
      if (!editor || !wikiMatch) {
        return;
      }

      let finalTitle = option.title;
      if (option.kind === "create") {
        if (!onCreateWikiLink) {
          return;
        }
        try {
          const created = await onCreateWikiLink(option.title);
          finalTitle = created.title;
        } catch {
          onEditorError?.("Failed to create linked note");
          return;
        }
      }

      editor
        .chain()
        .focus()
        .insertContentAt({ from: wikiMatch.from, to: wikiMatch.to }, `[[${finalTitle}]]`)
        .run();

      setWikiMatch(null);
      setWikiSuggestions([]);
      setWikiSelectedIndex(0);
    },
    [editor, onCreateWikiLink, onEditorError, wikiMatch],
  );

  const handleKeyboardAction = useCallback(
    (event: KeyboardEventLike): boolean => {
      const action = resolveEditorKeydownAction(
        {
          key: event.key,
          metaKey: event.metaKey,
          ctrlKey: event.ctrlKey,
        },
        {
          disabled,
          hasSlashMenu: Boolean(slashMatch) && commandItems.length > 0,
          hasPalette: paletteOpen && commandItems.length > 0,
          hasWikiMenu: Boolean(wikiMatch) && wikiOptions.length > 0,
        },
      );

      if (action === "none") {
        return false;
      }

      if (action === "open_palette") {
        event.preventDefault();
        setPaletteOpen(true);
        setPaletteQuery("");
        setPaletteSelectedIndex(0);
        setSlashMatch(null);
        return true;
      }

      if (action === "close_menus") {
        event.preventDefault();
        setPaletteOpen(false);
        setSlashMatch(null);
        setWikiMatch(null);
        return true;
      }

      if (action === "move_next") {
        event.preventDefault();
        if (wikiMatch && wikiOptions.length > 0) {
          setWikiSelectedIndex((current) => clampIndex(current + 1, wikiOptions.length));
          return true;
        }
        if (paletteOpen && commandItems.length > 0) {
          setPaletteSelectedIndex((current) => clampIndex(current + 1, commandItems.length));
          return true;
        }
        if (slashMatch && commandItems.length > 0) {
          setSlashSelectedIndex((current) => clampIndex(current + 1, commandItems.length));
          return true;
        }
        return false;
      }

      if (action === "move_prev") {
        event.preventDefault();
        if (wikiMatch && wikiOptions.length > 0) {
          setWikiSelectedIndex((current) => clampIndex(current - 1, wikiOptions.length));
          return true;
        }
        if (paletteOpen && commandItems.length > 0) {
          setPaletteSelectedIndex((current) => clampIndex(current - 1, commandItems.length));
          return true;
        }
        if (slashMatch && commandItems.length > 0) {
          setSlashSelectedIndex((current) => clampIndex(current - 1, commandItems.length));
          return true;
        }
        return false;
      }

      if (action === "wiki_select") {
        event.preventDefault();
        const option = wikiOptions[wikiSelectedIndex] ?? wikiOptions[0];
        if (option) {
          void applyWikiLink(option);
        }
        return true;
      }

      if (action === "slash_select") {
        event.preventDefault();
        const selectedIndex = paletteOpen ? paletteSelectedIndex : slashSelectedIndex;
        const selected = commandItems[selectedIndex] ?? commandItems[0];
        if (!selected) {
          return true;
        }

        const deleteRange = slashMatch
          ? {
              from: slashMatch.from,
              to: slashMatch.to,
            }
          : undefined;
        runCommand(selected.id, deleteRange);
        return true;
      }

      return false;
    },
    [
      applyWikiLink,
      commandItems,
      disabled,
      paletteOpen,
      paletteSelectedIndex,
      runCommand,
      slashMatch,
      slashSelectedIndex,
      wikiMatch,
      wikiOptions,
      wikiSelectedIndex,
    ],
  );

  useEffect(() => {
    keydownHandlerRef.current = handleKeyboardAction;
  }, [handleKeyboardAction]);

  if (!editor) {
    return null;
  }

  return (
    <div className="tiptap-container" onKeyDown={(event) => { void handleKeyboardAction(event); }}>
      <div className="editor-command-row" role="toolbar" aria-label="Editor formatting commands">
        {EDITOR_COMMANDS.map((command) => (
          <button
            key={command.id}
            type="button"
            className="editor-command-button"
            onClick={() => runCommand(command.id)}
            disabled={disabled}
            aria-label={command.label}
          >
            {command.label}
          </button>
        ))}
        <button
          type="button"
          className="editor-command-button"
          onClick={() => {
            setPaletteOpen(true);
            setPaletteQuery("");
            setPaletteSelectedIndex(0);
            setSlashMatch(null);
          }}
          disabled={disabled}
          aria-label="Open commands"
        >
          Commands
        </button>
      </div>

      {slashMatch && commandItems.length > 0 ? (
        <div className="editor-flyout" role="listbox" aria-label="Slash commands">
          {commandItems.map((command, index) => (
            <button
              key={`slash-${command.id}`}
              type="button"
              role="option"
              aria-selected={index === slashSelectedIndex}
              className={`editor-flyout-option${index === slashSelectedIndex ? " selected" : ""}`}
              onMouseDown={(event) => {
                event.preventDefault();
                runCommand(command.id, { from: slashMatch.from, to: slashMatch.to });
              }}
            >
              {command.label}
            </button>
          ))}
        </div>
      ) : null}

      {wikiMatch ? (
        <div className="editor-flyout" role="listbox" aria-label="Wiki links">
          {wikiLoading ? <p className="editor-flyout-loading">Loading links...</p> : null}
          {!wikiLoading && wikiOptions.length === 0 ? <p className="editor-flyout-loading">No matching notes</p> : null}
          {!wikiLoading
            ? wikiOptions.map((option, index) => (
                <button
                  key={`${option.kind}-${option.title}`}
                  type="button"
                  role="option"
                  aria-selected={index === wikiSelectedIndex}
                  className={`editor-flyout-option${index === wikiSelectedIndex ? " selected" : ""}`}
                  onMouseDown={(event) => {
                    event.preventDefault();
                    void applyWikiLink(option);
                  }}
                >
                  {option.kind === "create" ? `Create "${option.title}"` : option.title}
                </button>
              ))
            : null}
        </div>
      ) : null}

      {paletteOpen ? (
        <div className="editor-palette" aria-label="Command palette">
          <label className="sr-only" htmlFor="editor-command-search">
            Command search
          </label>
          <input
            id="editor-command-search"
            className="editor-command-input"
            aria-label="Command search"
            type="text"
            value={paletteQuery}
            onChange={(event) => {
              setPaletteQuery(event.target.value);
              setPaletteSelectedIndex(0);
            }}
          />
          <div role="listbox" aria-label="Editor commands">
            {commandItems.map((command, index) => (
              <button
                key={`palette-${command.id}`}
                type="button"
                role="option"
                aria-selected={index === paletteSelectedIndex}
                className={`editor-flyout-option${index === paletteSelectedIndex ? " selected" : ""}`}
                onMouseDown={(event) => {
                  event.preventDefault();
                  runCommand(command.id);
                }}
              >
                {command.label}
              </button>
            ))}
            {commandItems.length === 0 ? <p className="editor-flyout-loading">No commands found</p> : null}
          </div>
        </div>
      ) : null}

      <div className="tiptap-editor-shell">
        <EditorContent
          className="tiptap-editor"
          editor={editor}
          aria-label="TipTap editor"
          data-testid="tiptap-editor"
        />
      </div>
    </div>
  );
}
