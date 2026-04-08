"use client";

import { useRef, useState } from "react";
import { Modal } from "../ui/Modal";

export interface QuickCaptureResult {
  title: string;
  body: string;
}

interface QuickCaptureModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (result: QuickCaptureResult) => void;
}

function parseCapture(raw: string): QuickCaptureResult | null {
  const trimmed = raw.trim();
  if (!trimmed) return null;

  const lines = trimmed.split("\n");
  const firstLine = lines[0].trim();
  const title = firstLine || "Untitled";
  const body = lines.slice(1).join("\n").trim();
  return { title, body };
}

export function QuickCaptureModal({ isOpen, onClose, onSave }: QuickCaptureModalProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    const result = parseCapture(text);
    if (!result) return;
    onSave(result);
    setText("");
    onClose();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Quick Capture">
      <div className="quick-capture-body">
        <textarea
          ref={textareaRef}
          className="quick-capture-textarea"
          placeholder="Start typing..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          autoFocus
          rows={6}
        />
        <div className="quick-capture-footer">
          <span className="quick-capture-hint">
            {typeof navigator !== "undefined" && navigator.platform?.includes("Mac") ? "\u2318" : "Ctrl"}+Enter to save
          </span>
          <button
            type="button"
            className="quick-capture-submit"
            data-testid="quick-capture-submit"
            onClick={handleSubmit}
          >
            Save to Inbox
          </button>
        </div>
      </div>
    </Modal>
  );
}
