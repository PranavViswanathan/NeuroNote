"use client";

import { useEffect, useRef, useState } from "react";

interface FilterComboboxProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
  placeholder?: string;
}

export function FilterCombobox({
  label,
  value,
  onChange,
  options,
  placeholder = "All",
}: FilterComboboxProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = options.filter((opt) =>
    opt.toLowerCase().includes(value.toLowerCase()),
  );

  useEffect(() => {
    if (!open) return;
    function handleOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, [open]);

  return (
    <div ref={containerRef} className="filter-combobox">
      <span className="notes-filter-label">{label}</span>
      <div className="filter-combobox-input-wrap">
        <input
          ref={inputRef}
          type="text"
          className="notes-filter-input filter-combobox-input"
          value={value}
          placeholder={placeholder}
          aria-label={label}
          onChange={(e) => { onChange(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
        />
        {value && (
          <button
            type="button"
            className="filter-combobox-clear"
            aria-label={`Clear ${label}`}
            onClick={() => { onChange(""); inputRef.current?.focus(); }}
          >
            ×
          </button>
        )}
      </div>
      {open && (filtered.length > 0 || value) && (
        <div className="filter-combobox-dropdown" role="listbox">
          {value && !options.some((o) => o.toLowerCase() === value.toLowerCase()) && (
            <button
              type="button"
              className="filter-combobox-option filter-combobox-option--typed"
              role="option"
              aria-selected={false}
              onClick={() => { onChange(value); setOpen(false); }}
            >
              <span className="filter-combobox-match">{value}</span>
              <span className="filter-combobox-hint">filter by this</span>
            </button>
          )}
          {filtered.map((opt) => (
            <button
              key={opt}
              type="button"
              className={`filter-combobox-option${value.toLowerCase() === opt.toLowerCase() ? " selected" : ""}`}
              role="option"
              aria-selected={value.toLowerCase() === opt.toLowerCase()}
              onClick={() => { onChange(opt); setOpen(false); }}
            >
              {opt}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
