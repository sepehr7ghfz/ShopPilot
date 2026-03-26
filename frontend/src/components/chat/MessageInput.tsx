"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { ImageUploader } from "@/components/chat/ImageUploader";

interface MessageInputProps {
  isLoading: boolean;
  onSubmit: (payload: { message?: string; imageFile?: File | null }) => Promise<void>;
}

export function MessageInput({ isLoading, onSubmit }: MessageInputProps): JSX.Element {
  const [message, setMessage] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

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
    setSelectedFile(null);
  };

  return (
    <form className="message-input" onSubmit={handleSubmit}>
      <textarea
        className="message-input-textarea"
        disabled={isLoading}
        onChange={(event) => setMessage(event.target.value)}
        placeholder="Ask for recommendations, chat, or upload an image..."
        rows={3}
        value={message}
      />
      <div className="message-input-actions">
        <ImageUploader
          selectedFile={selectedFile}
          previewUrl={previewUrl}
          onFileSelected={setSelectedFile}
          disabled={isLoading}
        />
        <button className="message-send-button" disabled={isLoading} type="submit">
          {isLoading ? "Sending..." : "Send"}
        </button>
      </div>
    </form>
  );
}
