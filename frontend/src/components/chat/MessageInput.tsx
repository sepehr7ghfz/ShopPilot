"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { ImageUploader } from "@/components/chat/ImageUploader";

interface MessageInputProps {
  isLoading: boolean;
  selectedFile: File | null;
  onFileSelected: (file: File | null) => void;
  onSubmit: (payload: { message?: string; imageFile?: File | null }) => Promise<void>;
}

export function MessageInput({
  isLoading,
  selectedFile,
  onFileSelected,
  onSubmit,
}: MessageInputProps): JSX.Element {
  const [message, setMessage] = useState("");

  const previewUrl = useMemo(() => {
    if (!selectedFile) {
      return null;
    }
    return URL.createObjectURL(selectedFile);
  }, [selectedFile]);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();

    const trimmedMessage = message.trim();
    if (!trimmedMessage && !selectedFile) {
      return;
    }

    await onSubmit({
      message: trimmedMessage || undefined,
      imageFile: selectedFile,
    });

    setMessage("");
    onFileSelected(null);
  };

  return (
    <form className="message-input" onSubmit={handleSubmit}>
      <div className="message-input-top-row">
        <label className="message-input-label" htmlFor="assistant-message-input">
          Message
        </label>
        <span className="message-input-helper">Text, image, or both</span>
      </div>
      <div className="message-input-textarea-wrap">
        <textarea
          id="assistant-message-input"
          className="message-input-textarea"
          disabled={isLoading}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Ask for recommendations, describe what you need, or combine with an image..."
          rows={3}
          value={message}
        />
      </div>
      <div className="message-input-actions">
        <ImageUploader
          selectedFile={selectedFile}
          previewUrl={previewUrl}
          onFileSelected={onFileSelected}
          disabled={isLoading}
        />
        <button className="message-send-button" disabled={isLoading} type="submit">
          {isLoading ? "Sending..." : "Send"}
        </button>
      </div>
    </form>
  );
}
