"use client";

import { EditorContent, useEditor, type JSONContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { useEffect } from "react";

interface TipTapEditorProps {
  value: JSONContent;
  onUpdate: (payload: { json: JSONContent; text: string }) => void;
  onBlur: () => void;
}

export function TipTapEditor({ value, onUpdate, onBlur }: TipTapEditorProps) {
  const editor = useEditor({
    extensions: [StarterKit],
    content: value,
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
    editor.commands.setContent(value);
  }, [editor, value]);

  if (!editor) {
    return null;
  }

  return <EditorContent editor={editor} aria-label="TipTap editor" data-testid="tiptap-editor" />;
}
