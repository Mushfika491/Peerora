// A confirmation dialog that also asks for a short text (e.g. a ban reason).
import { useEffect, useId, useRef, useState } from "react";

interface PromptDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  inputLabel: string;
  required?: boolean;
  minLength?: number;
  confirmLabel: string;
  danger?: boolean;
  isProcessing?: boolean;
  onConfirm: (value: string) => void;
  onCancel: () => void;
}

function PromptDialog({
  isOpen,
  title,
  message,
  inputLabel,
  required = false,
  minLength = 0,
  confirmLabel,
  danger = false,
  isProcessing = false,
  onConfirm,
  onCancel,
}: PromptDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  // Unique ids, so several dialogs on one page never share a label target.
  const baseId = useId();
  const titleId = `${baseId}-title`;
  const inputId = `${baseId}-input`;
  const errorId = `${baseId}-error`;
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog === null) {
      return;
    }
    if (isOpen && !dialog.open) {
      setValue("");
      setError(null);
      dialog.showModal();
    } else if (!isOpen && dialog.open) {
      dialog.close();
    }
  }, [isOpen]);

  function handleConfirm() {
    const text = value.trim();
    if (required && text.length < Math.max(1, minLength)) {
      setError(`${inputLabel} must be at least ${Math.max(1, minLength)} characters.`);
      return;
    }
    onConfirm(text);
  }

  return (
    <dialog
      ref={dialogRef}
      className="confirm-dialog prompt-dialog"
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        if (!isProcessing) {
          onCancel();
        }
      }}
    >
      <div className="confirm-dialog-content">
        <h2 id={titleId}>{title}</h2>
        <p>{message}</p>
        <div className="form-field">
          <label htmlFor={inputId}>
            {inputLabel}
            {!required && <span className="muted"> (optional)</span>}
          </label>
          <textarea
            id={inputId}
            className="form-input"
            rows={3}
            maxLength={500}
            value={value}
            aria-invalid={error !== null}
            aria-describedby={error !== null ? errorId : undefined}
            onChange={(event) => {
              setValue(event.target.value);
              setError(null);
            }}
          />
          {error !== null && (
            <p className="form-error" id={errorId}>
              {error}
            </p>
          )}
        </div>
        <div className="confirm-dialog-actions">
          <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={isProcessing}>
            Cancel
          </button>
          <button
            type="button"
            className={danger ? "btn btn-danger" : "btn btn-primary"}
            onClick={handleConfirm}
            disabled={isProcessing}
          >
            {isProcessing ? "Please wait..." : confirmLabel}
          </button>
        </div>
      </div>
    </dialog>
  );
}

export default PromptDialog;
