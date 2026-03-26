import { ChangeEvent } from "react";

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
  const handleFileChange = (event: ChangeEvent<HTMLInputElement>): void => {
    const file = event.target.files?.[0] ?? null;
    onFileSelected(file);
  };

  return (
    <div className="image-uploader">
      <label className="image-uploader-label" htmlFor="assistant-image-upload">
        Attach image
      </label>
      <input
        id="assistant-image-upload"
        accept="image/*"
        className="image-uploader-input"
        disabled={disabled}
        onChange={handleFileChange}
        type="file"
      />
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
