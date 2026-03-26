import { DragEvent, useEffect, useRef } from "react";

import { ProductGrid } from "@/components/product/ProductGrid";
import { ChatMessage } from "@/lib/types";

interface MessageListProps {
  messages: ChatMessage[];
  onImageDropped: (file: File | null) => void;
}

export function MessageList({ messages, onImageDropped }: MessageListProps): JSX.Element {
  const listRef = useRef<HTMLDivElement | null>(null);
  const hasOnlyWelcome = messages.length === 1 && messages[0]?.id === "assistant-welcome";

  useEffect(() => {
    const listEl = listRef.current;
    if (!listEl) {
      return;
    }

    listEl.scrollTop = listEl.scrollHeight;
  }, [messages]);

  const handleDrop = (event: DragEvent<HTMLDivElement>): void => {
    event.preventDefault();
    const file = event.dataTransfer.files?.[0] ?? null;
    onImageDropped(file);
  };

  const handleDragOver = (event: DragEvent<HTMLDivElement>): void => {
    event.preventDefault();
  };

  return (
    <div ref={listRef} className="message-list" aria-live="polite" onDrop={handleDrop} onDragOver={handleDragOver}>
      {hasOnlyWelcome ? (
        <section className="message-list-empty-state" aria-label="Welcome help">
          <h3>Ready when you are</h3>
          <p>Start with text, image, or combine both for sharper recommendations.</p>
          <div className="message-list-empty-chips">
            <span>Type a request</span>
            <span>Drop an image</span>
            <span>Get ranked products</span>
          </div>
        </section>
      ) : null}
      {messages.map((message) => {
        const hasProducts = Boolean(message.products?.length);
        return (
          <div key={message.id} className={`message-row message-row-${message.role}`}>
            <article
              className={`message message-${message.role} ${message.isError ? "message-error" : ""} ${
                message.id === "assistant-welcome" ? "message-welcome" : ""
              } ${hasProducts ? "message-has-products" : ""}`}
            >
              <header className="message-header">
                <span className="message-role-pill">{message.role === "user" ? "You" : "ShopPilot"}</span>
                {message.intent ? <small>{message.intent}</small> : null}
              </header>
              <p className="message-text">{message.text}</p>
              {message.imagePreviewUrl ? (
                <div className="message-image-preview-wrap">
                  <img src={message.imagePreviewUrl} alt="Uploaded by user" className="message-image-preview" />
                </div>
              ) : null}
              {hasProducts ? <ProductGrid products={message.products ?? []} /> : null}
            </article>
          </div>
        );
      })}
    </div>
  );
}
