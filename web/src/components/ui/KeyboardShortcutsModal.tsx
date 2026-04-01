import { Modal } from "./Modal";

interface Shortcut {
  keys: string[];
  description: string;
}

interface ShortcutSection {
  title: string;
  shortcuts: Shortcut[];
}

const SHORTCUTS: ShortcutSection[] = [
  {
    title: "General",
    shortcuts: [
      { keys: ["?"], description: "Show keyboard shortcuts" },
      { keys: ["Ctrl", "K"], description: "Quick switch notes" },
      { keys: ["Escape"], description: "Close dialog / cancel" },
    ],
  },
  {
    title: "Editor",
    shortcuts: [
      { keys: ["Ctrl", "B"], description: "Bold" },
      { keys: ["Ctrl", "I"], description: "Italic" },
      { keys: ["Tab"], description: "Indent block" },
      { keys: ["Shift", "Tab"], description: "Outdent block" },
      { keys: ["[", "["], description: "Insert wiki-link" },
      { keys: ["(", "("], description: "Insert block reference" },
      { keys: ["/"], description: "Slash commands" },
    ],
  },
  {
    title: "Note List",
    shortcuts: [
      { keys: ["↑", "↓"], description: "Move between notes" },
      { keys: ["Enter"], description: "Open highlighted note" },
      { keys: ["Shift", "F10"], description: "Open context menu" },
    ],
  },
];

interface KeyboardShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function KeyboardShortcutsModal({ isOpen, onClose }: KeyboardShortcutsModalProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Keyboard Shortcuts">
      <div className="shortcuts-grid">
        {SHORTCUTS.map((section) => (
          <div key={section.title} className="shortcuts-section">
            <h3 className="shortcuts-section-title">{section.title}</h3>
            <div className="shortcuts-list">
              {section.shortcuts.map((shortcut, i) => (
                <div key={i} className="shortcut-item">
                  <div className="shortcut-keys">
                    {shortcut.keys.map((key, j) => (
                      <kbd key={j} className="shortcut-key">
                        {key}
                      </kbd>
                    ))}
                  </div>
                  <span className="shortcut-description">{shortcut.description}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Modal>
  );
}
