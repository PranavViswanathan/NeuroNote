"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Application error:", error);
  }, [error]);

  return (
    <div className="error-page">
      <div className="error-container">
        <h1>Something went wrong</h1>
        <p className="error-message">
          We encountered an unexpected error. Please try again.
        </p>
        {error.digest && <p className="error-digest">Error ID: {error.digest}</p>}
        <div className="error-actions">
          <button onClick={reset} className="primary">
            Try again
          </button>
          <button onClick={() => (window.location.href = "/")}>Go home</button>
        </div>
      </div>
    </div>
  );
}
