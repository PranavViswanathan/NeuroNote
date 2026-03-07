"use client";

import { EditorContent, useEditor, type JSONContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { useEffect } from "react";

export interface TipTapUpdatePayload {
  json: JSONContent;
  text: string;
}

interface TipTapEditorProps {
  value: JSONContent;
  onUpdate: (payload: TipTapUpdatePayload) => void;
  onBlur: () => void;
  disabled?: boolean;
}

export function TipTapEditor({ value, onUpdate, onBlur, disabled = false }: TipTapEditorProps) {
  const serializedValue = JSON.stringify(value);
  const editor = useEditor({
    extensions: [StarterKit],
    content: value,
    editable: !disabled,
    onUpdate: ({ editor: tiptapEditor }) => {
      onUpdate({
        json: tiptapEditor.getJSON(),
        text: tiptapEditor.getText(),
      });
    },
    onBlur: () => {
      onBlur();
    },
  });

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

  if (!editor) {
    return null;
  }

  return (
    <EditorContent
      editor={editor}
      aria-label="TipTap editor"
      data-testid="tiptap-editor"
    />
  );
}
