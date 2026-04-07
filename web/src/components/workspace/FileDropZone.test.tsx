import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FileDropZone } from "./FileDropZone";

describe("FileDropZone", () => {
  it("renders children", () => {
    render(
      <FileDropZone onFileContent={vi.fn()}>
        <span>child content</span>
      </FileDropZone>,
    );
    expect(screen.getByText("child content")).toBeTruthy();
  });

  it("shows overlay on dragover", () => {
    render(
      <FileDropZone onFileContent={vi.fn()}>
        <span>content</span>
      </FileDropZone>,
    );
    const zone = screen.getByTestId("file-drop-zone");
    fireEvent.dragOver(zone);
    expect(screen.getByTestId("file-drop-overlay")).toBeTruthy();
  });

  it("hides overlay on dragleave", () => {
    render(
      <FileDropZone onFileContent={vi.fn()}>
        <span>content</span>
      </FileDropZone>,
    );
    const zone = screen.getByTestId("file-drop-zone");
    fireEvent.dragOver(zone);
    expect(screen.getByTestId("file-drop-overlay")).toBeTruthy();
    fireEvent.dragLeave(zone);
    expect(screen.queryByTestId("file-drop-overlay")).toBeNull();
  });
});
