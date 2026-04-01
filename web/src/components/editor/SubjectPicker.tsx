"use client";

import { useState, useRef, useEffect, useId } from "react";

interface SubjectPickerProps {
  value: string;
  onChange: (subject: string) => void;
  suggestions: string[];
  disabled?: boolean;
}

export function SubjectPicker({ value, onChange, suggestions, disabled }: SubjectPickerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState(value);
  const containerRef = useRef<HTMLDivElement>(null);
  const listboxId = useId();

  // Keep local input in sync when value changes externally (note switch)
  useEffect(() => {
    setInputValue(value);
  }, [value]);

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [isOpen]);

  const filtered = suggestions.filter(
    (s) => s.toLowerCase().includes(inputValue.toLowerCase()) && s !== inputValue,
  );
  const showDropdown = isOpen && (filtered.length > 0 || (inputValue.trim() && !suggestions.includes(inputValue.trim())));

  const commit = (subject: string) => {
    const trimmed = subject.trim();
    setInputValue(trimmed);
    onChange(trimmed);
    setIsOpen(false);
  };

  return (
    <div className="picker-container" ref={containerRef}>
      <input
        className="note-editor-input picker-input"
        aria-label="Subject"
        aria-autocomplete="list"
        aria-controls={showDropdown ? listboxId : undefined}
        aria-expanded={!!showDropdown}
        type="text"
        value={inputValue}
        disabled={disabled}
        placeholder="inbox"
        autoComplete="off"
        onChange={(e) => {
          setInputValue(e.target.value);
          onChange(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        onKeyDown={(e) => {
          if (e.key === "Escape") setIsOpen(false);
          if (e.key === "Enter" && inputValue.trim()) {
            e.preventDefault();
            commit(inputValue);
          }
        }}
      />
      {showDropdown && (
        <ul
          id={listboxId}
          className="picker-dropdown"
          role="listbox"
          aria-label="Subject suggestions"
        >
          {filtered.map((subject) => (
            <li
              key={subject}
              role="option"
              aria-selected={false}
              className="picker-option"
              onMouseDown={(e) => {
                e.preventDefault(); // prevent input blur
                commit(subject);
              }}
            >
              {subject}
            </li>
          ))}
          {inputValue.trim() && !suggestions.includes(inputValue.trim()) && filtered.length === 0 && (
            <li
              role="option"
              aria-selected={false}
              className="picker-option picker-create"
              onMouseDown={(e) => {
                e.preventDefault();
                commit(inputValue);
              }}
            >
              Use &ldquo;{inputValue.trim()}&rdquo;
            </li>
          )}
        </ul>
      )}
    </div>
  );
}
