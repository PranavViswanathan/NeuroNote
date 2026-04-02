import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SubjectPicker } from "./SubjectPicker";

describe("SubjectPicker", () => {
  const defaultSuggestions = ["inbox", "work", "personal", "learning"];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders subject as a badge in display mode", () => {
    const onChange = vi.fn();
    render(
      <SubjectPicker value="inbox" onChange={onChange} suggestions={defaultSuggestions} />,
    );
    expect(screen.getByRole("button", { name: "inbox" })).toBeInTheDocument();
    expect(screen.queryByLabelText("Subject")).not.toBeInTheDocument();
  });

  it("renders placeholder button when value is empty", () => {
    const onChange = vi.fn();
    render(
      <SubjectPicker value="" onChange={onChange} suggestions={defaultSuggestions} />,
    );
    expect(screen.getByRole("button", { name: "Add subject…" })).toBeInTheDocument();
  });

  it("enters edit mode when badge is clicked", () => {
    const onChange = vi.fn();
    render(
      <SubjectPicker value="inbox" onChange={onChange} suggestions={defaultSuggestions} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "inbox" }));
    expect(screen.getByLabelText("Subject")).toBeInTheDocument();
  });

  it("shows suggestions dropdown on focus in edit mode", () => {
    const onChange = vi.fn();
    render(
      <SubjectPicker value="" onChange={onChange} suggestions={defaultSuggestions} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Add subject…" }));
    const input = screen.getByLabelText("Subject");
    fireEvent.focus(input);
    expect(screen.getByRole("listbox", { name: "Subject suggestions" })).toBeInTheDocument();
  });

  it("does not show dropdown when no suggestions exist and input is empty", () => {
    const onChange = vi.fn();
    render(<SubjectPicker value="" onChange={onChange} suggestions={[]} />);
    fireEvent.click(screen.getByRole("button", { name: "Add subject…" }));
    const input = screen.getByLabelText("Subject");
    fireEvent.focus(input);
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("filters suggestions based on input", () => {
    const onChange = vi.fn();
    render(
      <SubjectPicker value="" onChange={onChange} suggestions={defaultSuggestions} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Add subject…" }));
    const input = screen.getByLabelText("Subject");
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "in" } });
    const listbox = screen.getByRole("listbox", { name: "Subject suggestions" });
    expect(listbox).toHaveTextContent("inbox");
    expect(listbox).not.toHaveTextContent("work");
    expect(listbox).not.toHaveTextContent("personal");
  });

  it("calls onChange when suggestion is clicked", () => {
    const onChange = vi.fn();
    render(
      <SubjectPicker value="" onChange={onChange} suggestions={defaultSuggestions} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Add subject…" }));
    const input = screen.getByLabelText("Subject");
    fireEvent.focus(input);
    const option = screen.getByRole("option", { name: "inbox" });
    fireEvent.mouseDown(option);
    expect(onChange).toHaveBeenCalledWith("inbox");
  });

  it("calls onChange on Enter key with text in input", () => {
    const onChange = vi.fn();
    render(
      <SubjectPicker value="" onChange={onChange} suggestions={defaultSuggestions} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Add subject…" }));
    const input = screen.getByLabelText("Subject");
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "projects" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onChange).toHaveBeenCalledWith("projects");
  });

  it("shows 'Use ...' create option for unseen values", () => {
    const onChange = vi.fn();
    render(
      <SubjectPicker value="" onChange={onChange} suggestions={defaultSuggestions} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Add subject…" }));
    const input = screen.getByLabelText("Subject");
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "newsubject" } });
    expect(screen.getByRole("option", { name: /Use.*newsubject/ })).toBeInTheDocument();
  });

  it("clicking 'Use ...' calls onChange with typed value", () => {
    const onChange = vi.fn();
    render(
      <SubjectPicker value="" onChange={onChange} suggestions={defaultSuggestions} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Add subject…" }));
    const input = screen.getByLabelText("Subject");
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "newsubject" } });
    const createOption = screen.getByRole("option", { name: /Use.*newsubject/ });
    fireEvent.mouseDown(createOption);
    expect(onChange).toHaveBeenCalledWith("newsubject");
  });

  it("closes dropdown on Escape and returns to display mode", () => {
    const onChange = vi.fn();
    render(
      <SubjectPicker value="" onChange={onChange} suggestions={defaultSuggestions} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Add subject…" }));
    const input = screen.getByLabelText("Subject");
    fireEvent.focus(input);
    expect(screen.getByRole("listbox", { name: "Subject suggestions" })).toBeInTheDocument();
    fireEvent.keyDown(input, { key: "Escape" });
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("closes on outside click", () => {
    const onChange = vi.fn();
    render(
      <div>
        <SubjectPicker value="" onChange={onChange} suggestions={defaultSuggestions} />
        <button>Outside</button>
      </div>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Add subject…" }));
    const input = screen.getByLabelText("Subject");
    fireEvent.focus(input);
    expect(screen.getByRole("listbox", { name: "Subject suggestions" })).toBeInTheDocument();
    fireEvent.mouseDown(screen.getByRole("button", { name: "Outside" }));
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("renders badge as disabled when disabled prop is set", () => {
    const onChange = vi.fn();
    render(
      <SubjectPicker
        value="inbox"
        onChange={onChange}
        suggestions={defaultSuggestions}
        disabled
      />,
    );
    const badge = screen.getByRole("button", { name: "inbox" });
    expect(badge).toBeDisabled();
  });

  it("syncs value prop change when note switches", () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <SubjectPicker value="inbox" onChange={onChange} suggestions={defaultSuggestions} />,
    );
    expect(screen.getByRole("button", { name: "inbox" })).toBeInTheDocument();
    rerender(
      <SubjectPicker value="work" onChange={onChange} suggestions={defaultSuggestions} />,
    );
    expect(screen.getByRole("button", { name: "work" })).toBeInTheDocument();
  });
});
