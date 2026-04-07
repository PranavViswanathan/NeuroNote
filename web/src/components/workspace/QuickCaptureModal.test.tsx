import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { QuickCaptureModal } from "./QuickCaptureModal";

describe("QuickCaptureModal", () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onSave: vi.fn(),
  };

  it("renders textarea when open", () => {
    render(<QuickCaptureModal {...defaultProps} />);
    expect(screen.getByPlaceholderText("Start typing...")).toBeTruthy();
  });

  it("does not render when closed", () => {
    const { container } = render(<QuickCaptureModal {...defaultProps} isOpen={false} />);
    expect(container.innerHTML).toBe("");
  });

  it("extracts title from first non-empty line", () => {
    const onSave = vi.fn();
    render(<QuickCaptureModal {...defaultProps} onSave={onSave} />);
    const textarea = screen.getByPlaceholderText("Start typing...");
    fireEvent.change(textarea, { target: { value: "My Note Title\nSome body text" } });
    fireEvent.click(screen.getByTestId("quick-capture-submit"));
    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({ title: "My Note Title" }),
    );
  });

  it("falls back to Untitled when content is only whitespace", () => {
    const onSave = vi.fn();
    render(<QuickCaptureModal {...defaultProps} onSave={onSave} />);
    const textarea = screen.getByPlaceholderText("Start typing...");
    // Empty — should not submit at all
    fireEvent.change(textarea, { target: { value: "   " } });
    fireEvent.click(screen.getByTestId("quick-capture-submit"));
    expect(onSave).not.toHaveBeenCalled();
  });

  it("uses first line as title even with leading newlines (trimmed)", () => {
    const onSave = vi.fn();
    render(<QuickCaptureModal {...defaultProps} onSave={onSave} />);
    const textarea = screen.getByPlaceholderText("Start typing...");
    fireEvent.change(textarea, { target: { value: "\nSome body" } });
    fireEvent.click(screen.getByTestId("quick-capture-submit"));
    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({ title: "Some body" }),
    );
  });

  it("calls onClose on Escape", () => {
    const onClose = vi.fn();
    render(<QuickCaptureModal {...defaultProps} onClose={onClose} />);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });

  it("submits on Cmd+Enter", () => {
    const onSave = vi.fn();
    render(<QuickCaptureModal {...defaultProps} onSave={onSave} />);
    const textarea = screen.getByPlaceholderText("Start typing...");
    fireEvent.change(textarea, { target: { value: "Quick note" } });
    fireEvent.keyDown(textarea, { key: "Enter", metaKey: true });
    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({ title: "Quick note" }),
    );
  });

  it("does not submit when textarea is empty", () => {
    const onSave = vi.fn();
    render(<QuickCaptureModal {...defaultProps} onSave={onSave} />);
    fireEvent.click(screen.getByTestId("quick-capture-submit"));
    expect(onSave).not.toHaveBeenCalled();
  });
});
