"use client";

import { EditorContent, useEditor, type JSONContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { useCallback, useEffect, useMemo, useRef, useState, type ChangeEvent } from "react";
import { createPortal } from "react-dom";
import { InputModal } from "../ui/InputModal";

import {
  EDITOR_COMMANDS,
  filterEditorCommands,
  findSlashCommandMatch,
  type EditorCommandDefinition,
  type EditorCommandId,
  type SlashCommandMatch,
} from "../../lib/editor/commands";
import { ImageNode } from "../../lib/editor/extensions/image-node";
import { MathBlock } from "../../lib/editor/extensions/math-block";
import { MathInline } from "../../lib/editor/extensions/math-inline";
import { ReferenceLink } from "../../lib/editor/extensions/reference-link";
import { BlockHierarchy } from "../../lib/editor/extensions/block-hierarchy";
import {
  findBlockRefMatch,
  normalizeBlockRefToken,
  type BlockRefMatch,
} from "../../lib/editor/block-refs";
import {
  applyIndentAtIndex,
  applyOutdentAtIndex,
  computeHierarchyActions,
  formatHierarchyHint,
  resolveParentPreviewText,
} from "../../lib/editor/block-hierarchy";
import { normalizeMathLatex } from "../../lib/editor/math";
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

export interface BlockRefSuggestion {
  blockUid: string;
  noteId: string;
  noteTitle: string;
  contentText: string;
}

export interface UploadedImagePayload {
  assetId: string;
  src: string;
  mimeType: string;
}

interface TipTapEditorProps {
  value: JSONContent;
  onUpdate: (payload: TipTapUpdatePayload) => void;
  onBlur: () => void;
  disabled?: boolean;
  onUploadImage?: (file: File) => Promise<UploadedImagePayload>;
  onSearchWikiLinks?: (query: string) => Promise<WikiLinkSuggestion[]>;
  onCreateWikiLink?: (title: string) => Promise<WikiLinkSuggestion>;
  onSearchBlockRefs?: (query: string) => Promise<BlockRefSuggestion[]>;
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
  shiftKey: boolean;
  preventDefault: () => void;
}

export function TipTapEditor({
  value,
  onUpdate,
  onBlur,
  disabled = false,
  onUploadImage,
  onSearchWikiLinks,
  onCreateWikiLink,
  onSearchBlockRefs,
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
  const [blockRefMatch, setBlockRefMatch] = useState<BlockRefMatch | null>(null);
  const [blockRefSuggestions, setBlockRefSuggestions] = useState<BlockRefSuggestion[]>([]);
  const [blockRefSelectedIndex, setBlockRefSelectedIndex] = useState(0);
  const [blockRefLoading, setBlockRefLoading] = useState(false);
  const [hierarchyHint, setHierarchyHint] = useState<{
    canIndent: boolean;
    canOutdent: boolean;
    parentPreviewText: string | null;
    hintText: string;
  }>({
    canIndent: false,
    canOutdent: false,
    parentPreviewText: null,
    hintText: "No nesting action available for current block",
  });
  const [mathModalOpen, setMathModalOpen] = useState(false);
  const [mathMode, setMathMode] = useState<"inline" | "block">("inline");
  const [menuAnchor, setMenuAnchor] = useState<{ x: number; y: number } | null>(null);
  const wikiSearchTokenRef = useRef(0);
  const blockRefSearchTokenRef = useRef(0);
  const keydownHandlerRef = useRef<(event: KeyboardEventLike) => boolean>(() => false);
  const imageInputRef = useRef<HTMLInputElement | null>(null);

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

      if (!onSearchBlockRefs) {
        setBlockRefMatch(null);
      } else {
        const nextBlockRefMatch = findBlockRefMatch(editorTextBeforeCursor, blockStartPos);
        setBlockRefMatch(nextBlockRefMatch);
        if (!nextBlockRefMatch) {
          setBlockRefSuggestions([]);
        }
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
    [onSearchBlockRefs, onSearchWikiLinks],
  );

  const editor = useEditor({
    extensions: [StarterKit, BlockHierarchy, ReferenceLink, MathInline, MathBlock, ImageNode],
    content: value,
    editable: !disabled,
    immediatelyRender: false,
    onUpdate: ({ editor: tiptapEditor }) => {
      const { $from } = tiptapEditor.state.selection;
      const blockText = $from.parent.textContent.slice(0, $from.parentOffset);
      resolveInlineMenus(blockText, $from.start());
      const actions = computeHierarchyActions(tiptapEditor.getJSON(), $from.index(0));
      const parentPreviewText = resolveParentPreviewText(tiptapEditor.getJSON(), $from.index(0));
      setHierarchyHint({
        canIndent: actions.canIndent,
        canOutdent: actions.canOutdent,
        parentPreviewText,
        hintText: formatHierarchyHint({
          canIndent: actions.canIndent,
          canOutdent: actions.canOutdent,
          parentPreviewText,
        }),
      });

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
      const actions = computeHierarchyActions(tiptapEditor.getJSON(), $from.index(0));
      const parentPreviewText = resolveParentPreviewText(tiptapEditor.getJSON(), $from.index(0));
      setHierarchyHint({
        canIndent: actions.canIndent,
        canOutdent: actions.canOutdent,
        parentPreviewText,
        hintText: formatHierarchyHint({
          canIndent: actions.canIndent,
          canOutdent: actions.canOutdent,
          parentPreviewText,
        }),
      });
    },
    editorProps: {
      handleKeyDown: (_view, event) => keydownHandlerRef.current(event),
      handleClick: (_view, _pos, event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement)) {
          return false;
        }
        const link = target.closest("a[data-reference-link]") as HTMLAnchorElement | null;
        if (!link) {
          return false;
        }
        const href = link.getAttribute("href");
        if (!href) {
          return false;
        }
        event.preventDefault();
        window.location.href = href;
        return true;
      },
    },
  });

  useEffect(() => {
    if (!editor) return;
    const anyMatch = slashMatch ?? blockRefMatch ?? wikiMatch;
    if (anyMatch) {
      try {
        const pos = editor.state.selection.from;
        const coords = editor.view.coordsAtPos(pos);
        setMenuAnchor({ x: coords.left, y: coords.bottom });
      } catch {
        setMenuAnchor(null);
      }
    } else {
      setMenuAnchor(null);
    }
  }, [slashMatch, blockRefMatch, wikiMatch, editor]);

  const handleInsertMath = useCallback(
    (latex: string) => {
      if (!editor || !latex.trim()) return;

      const normalizedLatex = normalizeMathLatex(latex);
      if (!normalizedLatex) return;

      if (mathMode === "inline") {
        editor.chain().focus().insertContent({ type: "mathInline", attrs: { latex: normalizedLatex } }).run();
      } else {
        editor.chain().focus().insertContent({ type: "mathBlock", attrs: { latex: normalizedLatex } }).run();
      }
    },
    [editor, mathMode],
  );

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
    if (!blockRefMatch || !onSearchBlockRefs) {
      return;
    }

    const token = blockRefSearchTokenRef.current + 1;
    blockRefSearchTokenRef.current = token;
    setBlockRefLoading(true);

    void onSearchBlockRefs(normalizeBlockRefToken(blockRefMatch.query))
      .then((results) => {
        if (blockRefSearchTokenRef.current !== token) {
          return;
        }
        setBlockRefSuggestions(results);
        setBlockRefSelectedIndex(0);
      })
      .catch(() => {
        if (blockRefSearchTokenRef.current !== token) {
          return;
        }
        setBlockRefSuggestions([]);
      })
      .finally(() => {
        if (blockRefSearchTokenRef.current === token) {
          setBlockRefLoading(false);
        }
      });
  }, [blockRefMatch, onSearchBlockRefs]);

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

      let shouldRunChain = true;
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
        case "mathInline": {
          shouldRunChain = false;
          setMathMode("inline");
          setMathModalOpen(true);
          break;
        }
        case "mathBlock": {
          shouldRunChain = false;
          setMathMode("block");
          setMathModalOpen(true);
          break;
        }
        case "image":
          shouldRunChain = false;
          imageInputRef.current?.click();
          break;
        default:
          break;
      }

      if (shouldRunChain) {
        chain.run();
      }
      setSlashMatch(null);
      setSlashQuery("");
      setBlockRefMatch(null);
      setPaletteOpen(false);
      setPaletteQuery("");
    },
    [editor],
  );

  const handleImageSelection = useCallback(
    async (event: ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      event.target.value = "";
      if (!file) {
        return;
      }
      if (!onUploadImage) {
        onEditorError?.("Image upload is unavailable");
        return;
      }

      try {
        const uploaded = await onUploadImage(file);
        const extension = uploaded.mimeType.split("/")[1] ?? "bin";
        editor
          ?.chain()
          .focus()
          .insertContent({
            type: "image",
            attrs: {
              src: uploaded.src,
              alt: file.name,
              title: file.name,
              assetId: uploaded.assetId,
              filename: `${uploaded.assetId}.${extension}`,
              ext: extension,
            },
          })
          .run();
      } catch {
        onEditorError?.("Failed to upload image");
      }
    },
    [editor, onEditorError, onUploadImage],
  );

  const applyWikiLink = useCallback(
    async (option: WikiMenuOption) => {
      if (!editor || !wikiMatch) {
        return;
      }

      let finalTitle = option.title;
      let finalNoteId = option.kind === "existing" ? option.noteId : null;
      if (option.kind === "create") {
        if (!onCreateWikiLink) {
          return;
        }
        try {
          const created = await onCreateWikiLink(option.title);
          finalTitle = created.title;
          finalNoteId = created.noteId;
        } catch {
          onEditorError?.("Failed to create linked note");
          return;
        }
      }

      editor
        .chain()
        .focus()
        .insertContentAt(
          { from: wikiMatch.from, to: wikiMatch.to },
          {
            type: "text",
            text: `[[${finalTitle}]]`,
            marks: finalNoteId
              ? [
                  {
                    type: "referenceLink",
                    attrs: {
                      href: `/notes/${finalNoteId}`,
                      dataRefType: "note",
                      dataNoteId: finalNoteId,
                    },
                  },
                ]
              : [],
          },
        )
        .run();

      setWikiMatch(null);
      setWikiSuggestions([]);
      setWikiSelectedIndex(0);
    },
    [editor, onCreateWikiLink, onEditorError, wikiMatch],
  );

  const applyBlockRef = useCallback(
    (suggestion: BlockRefSuggestion) => {
      if (!editor || !blockRefMatch) {
        return;
      }

      editor
        .chain()
        .focus()
        .insertContentAt(
          { from: blockRefMatch.from, to: blockRefMatch.to },
          {
            type: "text",
            text: `↗ ${suggestion.noteTitle}`,
            marks: [
              {
                type: "referenceLink",
                attrs: {
                  href: `/notes/${suggestion.noteId}#block=${suggestion.blockUid}`,
                  dataRefType: "block",
                  dataNoteId: suggestion.noteId,
                  dataBlockUid: suggestion.blockUid,
                },
              },
            ],
          },
        )
        .run();

      setBlockRefMatch(null);
      setBlockRefSuggestions([]);
      setBlockRefSelectedIndex(0);
    },
    [blockRefMatch, editor],
  );

  const handleKeyboardAction = useCallback(
    (event: KeyboardEventLike): boolean => {
      const action = resolveEditorKeydownAction(
        {
          key: event.key,
          metaKey: event.metaKey,
          ctrlKey: event.ctrlKey,
          shiftKey: event.shiftKey,
        },
        {
          disabled,
          hasSlashMenu: Boolean(slashMatch) && commandItems.length > 0,
          hasPalette: paletteOpen && commandItems.length > 0,
          hasWikiMenu: Boolean(wikiMatch) && wikiOptions.length > 0,
          hasBlockRefMenu: Boolean(blockRefMatch) && blockRefSuggestions.length > 0,
          canIndentBlock: (editor?.can().sinkListItem("listItem") ?? false) || hierarchyHint.canIndent,
          canOutdentBlock: (editor?.can().liftListItem("listItem") ?? false) || hierarchyHint.canOutdent,
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
        setBlockRefMatch(null);
        return true;
      }

      if (action === "move_next") {
        event.preventDefault();
        if (blockRefMatch && blockRefSuggestions.length > 0) {
          setBlockRefSelectedIndex((current) => clampIndex(current + 1, blockRefSuggestions.length));
          return true;
        }
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

      if (action === "indent_block") {
        event.preventDefault();
        const canSinkList = editor?.can().sinkListItem("listItem") ?? false;
        if (canSinkList) {
          editor?.chain().focus().sinkListItem("listItem").run();
          return true;
        }
        if (editor) {
          const currentIndex = editor.state.selection.$from.index(0);
          const nextDoc = applyIndentAtIndex(editor.getJSON(), currentIndex);
          if (nextDoc) {
            editor.commands.setContent(nextDoc, false);
          }
        }
        return true;
      }

      if (action === "outdent_block") {
        event.preventDefault();
        const canLiftList = editor?.can().liftListItem("listItem") ?? false;
        if (canLiftList) {
          editor?.chain().focus().liftListItem("listItem").run();
          return true;
        }
        if (editor) {
          const currentIndex = editor.state.selection.$from.index(0);
          const nextDoc = applyOutdentAtIndex(editor.getJSON(), currentIndex);
          if (nextDoc) {
            editor.commands.setContent(nextDoc, false);
          }
        }
        return true;
      }

      if (action === "move_prev") {
        event.preventDefault();
        if (blockRefMatch && blockRefSuggestions.length > 0) {
          setBlockRefSelectedIndex((current) => clampIndex(current - 1, blockRefSuggestions.length));
          return true;
        }
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

      if (action === "block_ref_select") {
        event.preventDefault();
        const selected = blockRefSuggestions[blockRefSelectedIndex] ?? blockRefSuggestions[0];
        if (selected) {
          applyBlockRef(selected);
        }
        return true;
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
      applyBlockRef,
      blockRefMatch,
      blockRefSelectedIndex,
      blockRefSuggestions,
      commandItems,
      disabled,
      hierarchyHint.canIndent,
      hierarchyHint.canOutdent,
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
    <>
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
      <input
        ref={imageInputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp,image/gif"
        className="sr-only"
        aria-label="Upload image"
        onChange={(event) => {
          void handleImageSelection(event);
        }}
      />
      <p className="editor-hierarchy-hint" aria-live="polite">
        {hierarchyHint.hintText}
      </p>


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

      <InputModal
        isOpen={mathModalOpen}
        onClose={() => setMathModalOpen(false)}
        onSubmit={handleInsertMath}
        title={mathMode === "inline" ? "Insert Inline Math" : "Insert Block Math"}
        label="LaTeX expression"
        placeholder={mathMode === "inline" ? "x^2 + y^2" : "\\int_0^1 x \\, dx"}
      />
    </div>

    {slashMatch && menuAnchor && commandItems.length > 0
      ? createPortal(
          <div
            className="editor-flyout editor-flyout--anchored"
            role="listbox"
            aria-label="Slash commands"
            style={{ position: "fixed", left: menuAnchor.x, top: menuAnchor.y + 6 }}
          >
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
          </div>,
          document.body,
        )
      : null}

    {blockRefMatch && menuAnchor
      ? createPortal(
          <div
            className="editor-flyout editor-flyout--anchored"
            role="listbox"
            aria-label="Block references"
            style={{ position: "fixed", left: menuAnchor.x, top: menuAnchor.y + 6 }}
          >
            {blockRefLoading ? <p className="editor-flyout-loading">Searching blocks...</p> : null}
            {!blockRefLoading && blockRefSuggestions.length === 0 ? (
              <p className="editor-flyout-loading">No matching blocks</p>
            ) : null}
            {!blockRefLoading
              ? blockRefSuggestions.map((suggestion, index) => (
                  <button
                    key={`${suggestion.noteId}:${suggestion.blockUid}`}
                    type="button"
                    role="option"
                    aria-selected={index === blockRefSelectedIndex}
                    className={`editor-flyout-option${index === blockRefSelectedIndex ? " selected" : ""}`}
                    onMouseDown={(event) => {
                      event.preventDefault();
                      applyBlockRef(suggestion);
                    }}
                  >
                    <span>{suggestion.noteTitle}</span>
                    <small>{suggestion.contentText.slice(0, 72)}</small>
                  </button>
                ))
              : null}
          </div>,
          document.body,
        )
      : null}

    {wikiMatch && menuAnchor
      ? createPortal(
          <div
            className="editor-flyout editor-flyout--anchored"
            role="listbox"
            aria-label="Wiki links"
            style={{ position: "fixed", left: menuAnchor.x, top: menuAnchor.y + 6 }}
          >
            {wikiLoading ? <p className="editor-flyout-loading">Loading links...</p> : null}
            {!wikiLoading && wikiOptions.length === 0 ? (
              <p className="editor-flyout-loading">No matching notes</p>
            ) : null}
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
          </div>,
          document.body,
        )
      : null}
    </>
  );
}
