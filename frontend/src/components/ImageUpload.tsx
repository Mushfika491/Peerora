import { useEffect, useState } from "react";
import type { ChangeEvent } from "react";
import { IMAGE_ACCEPT_ATTRIBUTE, validateProfileImage } from "../utils/validation";
import FormField from "./FormField";

interface ImageUploadProps {
  id: string;
  label: string;
  file: File | null; // the newly chosen file (not uploaded yet)
  existingUrl: string; // an already saved picture ("" if there is none)
  onFileChange: (file: File | null) => void;
  onRemoveExisting: () => void; // asks the parent to forget the saved picture
  hint?: string;
  error?: string; // an error supplied by the parent (for example on submit)
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function ImageUpload({
  id,
  label,
  file,
  existingUrl,
  onFileChange,
  onRemoveExisting,
  hint = "JPG, JPEG, PNG or WebP. Maximum size 2 MB.",
  error,
}: ImageUploadProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [selectionError, setSelectionError] = useState<string | undefined>(
    undefined
  );
  const [existingFailed, setExistingFailed] = useState(false);

  // Create a temporary browser address for the chosen file so it can be
  // previewed, and release it when the file changes or the component closes.
  // This is a local preview only. It is not an uploaded file or a stored URL.
  useEffect(() => {
    if (file === null) {
      setPreviewUrl(null);
      return;
    }
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
    return () => {
      URL.revokeObjectURL(objectUrl);
    };
  }, [file]);

  // A new saved address gets a fresh chance to load.
  useEffect(() => {
    setExistingFailed(false);
  }, [existingUrl]);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selected: File | undefined = event.target.files?.[0];

    // Reset the input so choosing the same file again still triggers a change.
    event.target.value = "";

    if (selected === undefined) {
      return;
    }

    const message = validateProfileImage(selected);
    if (message !== undefined) {
      // An invalid file is rejected and the previous picture is kept.
      setSelectionError(message);
      return;
    }

    setSelectionError(undefined);
    onFileChange(selected);
  }

  // "Remove" clears both the newly chosen file and the saved picture.
  function handleRemove() {
    setSelectionError(undefined);
    onFileChange(null);
    onRemoveExisting();
  }

  const hasExisting = existingUrl !== "";
  const hasImage = file !== null || hasExisting;

  let previewContent;
  if (file !== null && previewUrl !== null) {
    previewContent = (
      <img src={previewUrl} alt="Preview of the selected profile picture" />
    );
  } else if (file === null && hasExisting && !existingFailed) {
    previewContent = (
      <img
        src={existingUrl}
        alt="Current profile picture"
        onError={() => setExistingFailed(true)}
      />
    );
  } else if (file === null && hasExisting && existingFailed) {
    previewContent = <span>Image could not be loaded</span>;
  } else {
    previewContent = <span>No photo</span>;
  }

  return (
    <FormField id={id} label={label} hint={hint} error={selectionError ?? error}>
      {(control) => (
        <div className="image-upload">
          <div className="image-upload-preview">{previewContent}</div>

          <div className="image-upload-body">
            {file !== null && (
              <p className="image-upload-filename">
                {file.name} ({formatFileSize(file.size)}) &ndash; selected, not
                uploaded yet
              </p>
            )}
            {file === null && hasExisting && (
              <p className="image-upload-filename">Current saved picture</p>
            )}

            <div className="image-upload-actions">
              {/* The real file input is visually hidden but stays focusable.
                  The label below acts as its visible button. */}
              <input
                {...control}
                type="file"
                className="file-input"
                accept={IMAGE_ACCEPT_ATTRIBUTE}
                onChange={handleFileChange}
              />
              <label htmlFor={id} className="btn btn-secondary file-trigger">
                {hasImage ? "Replace image" : "Choose image"}
              </label>

              {hasImage && (
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleRemove}
                >
                  Remove image
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </FormField>
  );
}

export default ImageUpload;