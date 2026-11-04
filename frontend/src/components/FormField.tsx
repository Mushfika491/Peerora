import type { ReactNode } from "react";

// The accessibility attributes that FormField hands to the control it wraps.
// The control must apply all of them (for example with {...control}).
export interface FieldControlProps {
  id: string;
  "aria-invalid": boolean;
  "aria-describedby": string | undefined;
  "aria-required": boolean | undefined;
}

interface FormFieldProps {
  id: string; // id of the control; the label points to it
  label: string;
  required?: boolean;
  hint?: string; // helper text shown below the control
  error?: string; // validation message; the field is marked invalid when present
  counter?: string; // e.g. "120 / 500", shown at the right of the helper text
  children: (control: FieldControlProps) => ReactNode;
}

function FormField({
  id,
  label,
  required = false,
  hint,
  error,
  counter,
  children,
}: FormFieldProps) {
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;
  const counterId = `${id}-counter`;

  // Screen readers read these elements when the control receives focus.
  // The error comes first because it is the most important message.
  const describedByIds: string[] = [];
  if (error !== undefined) {
    describedByIds.push(errorId);
  }
  if (hint !== undefined) {
    describedByIds.push(hintId);
  }
  if (counter !== undefined) {
    describedByIds.push(counterId);
  }

  const control: FieldControlProps = {
    id,
    "aria-invalid": error !== undefined,
    "aria-describedby":
      describedByIds.length > 0 ? describedByIds.join(" ") : undefined,
    "aria-required": required ? true : undefined,
  };

  return (
    <div className="form-field">
      <label htmlFor={id}>
        {label}
        {required && (
          <span className="required-mark" aria-hidden="true">
            {" "}
            *
          </span>
        )}
      </label>

      {children(control)}

      {error !== undefined && (
        <p className="form-error" id={errorId}>
          {error}
        </p>
      )}

      {(hint !== undefined || counter !== undefined) && (
        <div className="form-meta">
          {hint !== undefined && (
            <p className="form-hint" id={hintId}>
              {hint}
            </p>
          )}
          {counter !== undefined && (
            <p className="form-counter" id={counterId}>
              {counter}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default FormField;