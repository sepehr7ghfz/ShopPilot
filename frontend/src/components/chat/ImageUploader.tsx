import { ChangeEvent, useRef } from "react";

interface ImageUploaderProps {
  selectedFile: File | null;
  previewUrl: string | null;
  onFileSelected: (file: File | null) => void;
  disabled?: boolean;
}

export function ImageUploader({
  selectedFile,
  previewUrl,
  onFileSelected,
  disabled = false,
}: ImageUploaderProps): JSX.Element {
  const inputRef = useRef<HTMLInputElement | null>(null);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>): void => {
    const file = event.target.files?.[0] ?? null;
    onFileSelected(file);
  };

  return (
    <div className="image-uploader">
      <input
        id="assistant-image-upload"
        accept="image/*"
        className="image-uploader-input"
        disabled={disabled}
        onChange={handleFileChange}
        ref={inputRef}
        type="file"
      />
      <button
        className={`image-uploader-trigger ${disabled ? "is-disabled" : ""}`}
        aria-label="Choose image"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        type="button"
      >
        📎
      </button>
      {selectedFile && previewUrl ? (
        <div className="image-uploader-preview">
          <img src={previewUrl} alt="Selected upload preview" />
          <div className="image-uploader-meta">
            <span>{selectedFile.name}</span>
            <button disabled={disabled} onClick={() => onFileSelected(null)} type="button">
              Remove
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
