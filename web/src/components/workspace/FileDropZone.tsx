"use client";

import { useCallback, useState, type DragEvent, type ReactNode } from "react";

const ACCEPTED_EXTENSIONS = new Set(["md", "txt"]);

interface FileDropZoneProps {
  onFileContent: (filename: string, content: string) => void;
  children: ReactNode;
}

function getExtension(filename: string): string {
  const parts = filename.split(".");
  return parts.length > 1 ? (parts.pop() ?? "").toLowerCase() : "";
}

export function FileDropZone({ onFileContent, children }: FileDropZoneProps) {
  const [dragging, setDragging] = useState(false);

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragging(false);

      const files = Array.from(e.dataTransfer.files);
      for (const file of files) {
        const ext = getExtension(file.name);
        if (!ACCEPTED_EXTENSIONS.has(ext)) continue;

        const reader = new FileReader();
        reader.onload = () => {
          if (typeof reader.result === "string") {
            onFileContent(file.name, reader.result);
          }
        };
        reader.readAsText(file);
      }
    },
    [onFileContent],
  );

  return (
    <div
      className="file-drop-zone"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      data-testid="file-drop-zone"
    >
      {dragging && (
        <div className="file-drop-overlay" data-testid="file-drop-overlay">
          <span className="file-drop-label">Drop .md or .txt to import</span>
        </div>
      )}
      {children}
    </div>
  );
}
