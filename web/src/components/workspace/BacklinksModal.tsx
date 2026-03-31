"use client";

import type { BacklinkItem } from "../../../../shared/contracts/ts/v1/backlink";
import { ErrorMessage } from "../ui/ErrorMessage";

interface BacklinksModalProps {
  isOpen: boolean;
  noteTitle: string;
  items: BacklinkItem[];
  isLoading: boolean;
  errorMessage: string | null;
  onClose: () => void;
  onRetry: () => void;
  onOpenSource: (noteId: string) => void;
}

export function BacklinksModal({
  isOpen,
  noteTitle,
  items,
  isLoading,
  errorMessage,
  onClose,
  onRetry,
  onOpenSource,
}: BacklinksModalProps) {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="backlinks-modal-overlay" role="presentation" onClick={onClose}>
      <section
        aria-label="Linked mentions"
        aria-modal="true"
        className="backlinks-modal"
        role="dialog"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="backlinks-modal-header">
          <h2>Linked mentions for {noteTitle}</h2>
          <button type="button" className="backlinks-close-button" onClick={onClose}>
            Close
          </button>
        </header>
        {isLoading ? <p>Loading linked mentions...</p> : null}
        {errorMessage ? (
          <ErrorMessage
            message={errorMessage}
            actionLabel="Retry"
            onAction={onRetry}
          />
        ) : null}
        {!isLoading && !errorMessage && items.length === 0 ? <p>No linked mentions yet.</p> : null}
        {!isLoading && !errorMessage && items.length > 0 ? (
          <ul aria-label="Backlink sources" className="backlinks-modal-list">
            {items.map((item) => (
              <li key={item.source_note_id}>
                <button type="button" onClick={() => onOpenSource(item.source_note_id)}>
                  <span>{item.source_note_title}</span>
                  <span>{item.snippet}</span>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </section>
    </div>
  );
}
