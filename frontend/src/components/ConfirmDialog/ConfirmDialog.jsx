import { useEffect, useRef } from "react";

import "./ConfirmDialog.css";

export default function ConfirmDialog({
  open,
  title = "Tem certeza?",
  message,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  onConfirm,
  onCancel,
}) {
  const dialogRef = useRef(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  return (
    <dialog
      ref={dialogRef}
      className="confirm-dialog"
      onCancel={(event) => {
        event.preventDefault();
        onCancel();
      }}
      onClick={(event) => {
        if (event.target === dialogRef.current) onCancel();
      }}
    >
      <h2 className="confirm-dialog__title">{title}</h2>
      {message && <p className="confirm-dialog__message">{message}</p>}
      <div className="confirm-dialog__actions">
        <button
          type="button"
          className="confirm-dialog__button confirm-dialog__button--cancel"
          onClick={onCancel}
        >
          {cancelLabel}
        </button>
        <button
          type="button"
          className="confirm-dialog__button confirm-dialog__button--confirm"
          onClick={onConfirm}
        >
          {confirmLabel}
        </button>
      </div>
    </dialog>
  );
}
