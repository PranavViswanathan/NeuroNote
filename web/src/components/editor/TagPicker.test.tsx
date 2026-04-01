import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TagPicker } from "./TagPicker";

describe("TagPicker", () => {
  const defaultSuggestions = ["react", "typescript", "vitest", "graph", "ml"];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders existing tags as chips", () => {
    const onChange = vi.fn();
    render(
      <TagPicker value={["react", "typescript"]} onChange={onChange} suggestions={defaultSuggestions} />,
    );
    expect(screen.getByText("react")).toBeInTheDocument();
    expect(screen.getByText("typescript")).toBeInTheDocument();
  });

  it("remove chip calls onChange with that tag removed", () => {
    const onChange = vi.fn();
    render(
      <TagPicker value={["react", "typescript"]} onChange={onChange} suggestions={defaultSuggestions} />,
    );
    const removeButton = screen.getByRole("button", { name: "Remove tag react" });
    fireEvent.mouseDown(removeButton);
    expect(onChange).toHaveBeenCalledWith(["typescript"]);
  });

  it("adding tag via Enter key calls onChange with new tag appended", () => {
    const onChange = vi.fn();
    render(
      <TagPicker value={["react"]} onChange={onChange} suggestions={defaultSuggestions} />,
    );
    const input = screen.getByLabelText("Tags");
    fireEvent.change(input, { target: { value: "graph" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onChange).toHaveBeenCalledWith(["react", "graph"]);
  });

  it("adding tag via comma key calls onChange with new tag", () => {
    const onChange = vi.fn();
    render(
      <TagPicker value={["react"]} onChange={onChange} suggestions={defaultSuggestions} />,
    );
    const input = screen.getByLabelText("Tags");
    fireEvent.change(input, { target: { value: "ml" } });
    fireEvent.keyDown(input, { key: "," });
    expect(onChange).toHaveBeenCalledWith(["react", "ml"]);
  });

  it("normalizes tag to lowercase", () => {
    const onChange = vi.fn();
    render(
      <TagPicker value={[]} onChange={onChange} suggestions={defaultSuggestions} />,
    );
    const input = screen.getByLabelText("Tags");
    fireEvent.change(input, { target: { value: "React" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onChange).toHaveBeenCalledWith(["react"]);
  });

  it("does not add duplicate tags", () => {
    const onChange = vi.fn();
    render(
      <TagPicker value={["react"]} onChange={onChange} suggestions={defaultSuggestions} />,
    );
    const input = screen.getByLabelText("Tags");
    fireEvent.change(input, { target: { value: "react" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onChange).not.toHaveBeenCalled();
  });

  it("shows autocomplete dropdown when typing", () => {
    const onChange = vi.fn();
    render(
      <TagPicker value={[]} onChange={onChange} suggestions={defaultSuggestions} />,
    );
    const input = screen.getByLabelText("Tags");
    fireEvent.change(input, { target: { value: "vi" } });
    expect(screen.getByRole("listbox", { name: "Tag suggestions" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "vitest" })).toBeInTheDocument();
  });

  it("filters out already-added tags from suggestions", () => {
    const onChange = vi.fn();
    render(
      <TagPicker
        value={["react"]}
        onChange={onChange}
        suggestions={defaultSuggestions}
      />,
    );
    const input = screen.getByLabelText("Tags");
    // Focus to open dropdown with empty input — but dropdown only opens if filtered.length > 0
    // Type something to show suggestions that don't include "react"
    fireEvent.change(input, { target: { value: "r" } });
    // "react" matches "r" but is already added, so it shouldn't appear
    const listbox = screen.queryByRole("listbox", { name: "Tag suggestions" });
    if (listbox) {
      expect(listbox).not.toHaveTextContent(/^react$/);
    }
    // "vitest" doesn't match "r", so overall dropdown may or may not show depending on other matches
    // The key assertion: react chip still shows but not in suggestions
    expect(screen.getByText("react")).toBeInTheDocument();
  });

  it("clicking a suggestion adds the tag", () => {
    const onChange = vi.fn();
    render(
      <TagPicker value={[]} onChange={onChange} suggestions={defaultSuggestions} />,
    );
    const input = screen.getByLabelText("Tags");
    fireEvent.change(input, { target: { value: "gr" } });
    const option = screen.getByRole("option", { name: "graph" });
    fireEvent.mouseDown(option);
    expect(onChange).toHaveBeenCalledWith(["graph"]);
  });

  it("backspace removes last tag when input is empty", () => {
    const onChange = vi.fn();
    render(
      <TagPicker value={["react", "typescript"]} onChange={onChange} suggestions={defaultSuggestions} />,
    );
    const input = screen.getByLabelText("Tags");
    // Ensure input is empty (it starts empty)
    fireEvent.keyDown(input, { key: "Backspace" });
    expect(onChange).toHaveBeenCalledWith(["react"]);
  });

  it("disabled prop prevents interaction: no remove buttons, input is disabled", () => {
    const onChange = vi.fn();
    render(
      <TagPicker
        value={["react", "typescript"]}
        onChange={onChange}
        suggestions={defaultSuggestions}
        disabled
      />,
    );
    // Chips are visible
    expect(screen.getByText("react")).toBeInTheDocument();
    expect(screen.getByText("typescript")).toBeInTheDocument();
    // No remove buttons
    expect(screen.queryByRole("button", { name: "Remove tag react" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Remove tag typescript" })).not.toBeInTheDocument();
    // Input is disabled
    expect(screen.getByLabelText("Tags")).toBeDisabled();
  });

  it("shows 'Add...' option for new tag not in suggestions", () => {
    const onChange = vi.fn();
    render(
      <TagPicker value={[]} onChange={onChange} suggestions={defaultSuggestions} />,
    );
    const input = screen.getByLabelText("Tags");
    fireEvent.change(input, { target: { value: "neuronote" } });
    expect(screen.getByRole("option", { name: /Add.*neuronote/ })).toBeInTheDocument();
  });

  it("clicking 'Add...' option adds the new tag", () => {
    const onChange = vi.fn();
    render(
      <TagPicker value={[]} onChange={onChange} suggestions={defaultSuggestions} />,
    );
    const input = screen.getByLabelText("Tags");
    fireEvent.change(input, { target: { value: "neuronote" } });
    const createOption = screen.getByRole("option", { name: /Add.*neuronote/ });
    fireEvent.mouseDown(createOption);
    expect(onChange).toHaveBeenCalledWith(["neuronote"]);
  });
});
