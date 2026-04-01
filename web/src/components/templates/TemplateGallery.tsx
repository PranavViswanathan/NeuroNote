"use client";

import { useState } from "react";
import { Modal } from "../ui/Modal";
import {
  TEMPLATES,
  type Template,
  type TemplateCategory,
} from "../../lib/templates";

interface TemplateGalleryProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (template: Template) => void;
}

const ALL_CATEGORIES: TemplateCategory[] = [
  "daily",
  "meeting",
  "project",
  "reading",
  "blank",
];

export function TemplateGallery({
  isOpen,
  onClose,
  onSelect,
}: TemplateGalleryProps) {
  const [activeCategory, setActiveCategory] =
    useState<TemplateCategory | null>(null);

  const filtered =
    activeCategory === null
      ? TEMPLATES
      : TEMPLATES.filter((t) => t.category === activeCategory);

  function handleSelect(template: Template) {
    onSelect(template);
    onClose();
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Choose a template">
      {/* Category filter row */}
      <div className="template-gallery-filters">
        <button
          className={`btn btn-sm ${activeCategory === null ? "btn-primary" : "btn-ghost"}`}
          onClick={() => setActiveCategory(null)}
        >
          All
        </button>
        {ALL_CATEGORIES.map((cat) => (
          <button
            key={cat}
            className={`btn btn-sm ${activeCategory === cat ? "btn-primary" : "btn-ghost"}`}
            onClick={() => setActiveCategory(cat)}
          >
            {cat.charAt(0).toUpperCase() + cat.slice(1)}
          </button>
        ))}
      </div>

      {/* Template grid */}
      <div className="template-gallery-grid">
        {filtered.map((template) => (
          <button
            key={template.id}
            className="template-card"
            onClick={() => handleSelect(template)}
          >
            <span className="template-card-name">{template.name}</span>
            <span className="template-card-description">
              {template.description}
            </span>
            <span className="template-card-badge">{template.category}</span>
          </button>
        ))}
      </div>
    </Modal>
  );
}
