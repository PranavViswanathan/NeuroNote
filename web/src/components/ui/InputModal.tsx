import { useState, useEffect, FormEvent } from "react";
import { Modal } from "./Modal";
import { Button } from "./Button";

interface InputModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (value: string) => void;
  title: string;
  label: string;
  initialValue?: string;
  placeholder?: string;
  required?: boolean;
}

export function InputModal({
  isOpen,
  onClose,
  onSubmit,
  title,
  label,
  initialValue = "",
  placeholder,
  required = false,
}: InputModalProps) {
  const [value, setValue] = useState(initialValue);

  useEffect(() => {
    if (isOpen) {
      setValue(initialValue);
    }
  }, [isOpen, initialValue]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (required && !value.trim()) return;
    onSubmit(value);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
      <form onSubmit={handleSubmit}>
        <label htmlFor="modal-input">{label}</label>
        <input
          id="modal-input"
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={placeholder}
          autoFocus
          required={required}
        />
        <div className="modal-actions">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="primary" type="submit">
            OK
          </Button>
        </div>
      </form>
    </Modal>
  );
}
