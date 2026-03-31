interface ErrorMessageProps {
  message: string;
  actionLabel?: string;
  onAction?: () => void;
  compact?: boolean;
}

export function ErrorMessage({ message, actionLabel, onAction, compact = false }: ErrorMessageProps) {
  return (
    <div className={`error-message-inline ${compact ? "error-message-compact" : ""}`} role="alert">
      <span className="error-message-icon" aria-hidden="true">⚠</span>
      <span className="error-message-text">{message}</span>
      {actionLabel && onAction && (
        <button type="button" className="error-message-action" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </div>
  );
}
