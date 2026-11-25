import { useEffect, useId, useRef } from "react";

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  isProcessing?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  isProcessing = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  // A reference to the real <dialog> element in the browser's DOM.
  const dialogRef = useRef<HTMLDialogElement>(null);
  // Unique ids, so several dialogs on one page never share an aria target.
  const baseId = useId();
  const titleId = `${baseId}-title`;
  const messageId = `${baseId}-message`;

  // Open or close the native dialog whenever "isOpen" changes.
  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog === null) {
      return;
    }

    if (isOpen && !dialog.open) {
      dialog.showModal();
    } else if (!isOpen && dialog.open) {
      dialog.close();
    }
  }, [isOpen]);

  // Fired when the user presses the Escape key.
  function handleCancelEvent(event: React.SyntheticEvent<HTMLDialogElement>) {
    // Stop the browser from closing the dialog itself. The parent controls
    // it through the "isOpen" prop.
    event.preventDefault();
    if (!isProcessing) {
      onCancel();
    }
  }

  // Clicking the dimmed area outside the dialog box cancels it.
  function handleBackdropClick(event: React.MouseEvent<HTMLDialogElement>) {
    if (event.target === event.currentTarget && !isProcessing) {
      onCancel();
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className="confirm-dialog"
      aria-labelledby={titleId}
      aria-describedby={messageId}
      onCancel={handleCancelEvent}
      onClick={handleBackdropClick}
    >
      <div className="confirm-dialog-content">
        <h2 id={titleId}>{title}</h2>
        <p id={messageId}>{message}</p>

        <div className="confirm-dialog-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onCancel}
            disabled={isProcessing}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            className="btn btn-danger"
            onClick={onConfirm}
            disabled={isProcessing}
          >
            {isProcessing ? "Please wait..." : confirmLabel}
          </button>
        </div>
      </div>
    </dialog>
  );
}

export default ConfirmDialog;