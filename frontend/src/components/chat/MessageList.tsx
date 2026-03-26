import { DragEvent, Fragment, ReactNode, useEffect, useRef } from "react";

import { ProductGrid } from "@/components/product/ProductGrid";
import { ChatMessage } from "@/lib/types";

interface MessageListProps {
  messages: ChatMessage[];
  onImageDropped: (file: File | null) => void;
}

function normalizeAssistantText(text: string): string {
  return text
    .replace(/\s+(\d+\.\s\*\*)/g, "\n$1")
    .replace(/\s+-\s+\*\*Price:\*\*/g, "\n- **Price:**")
    .replace(/\s+-\s+\*\*Description:\*\*/g, "\n- **Description:**")
    .replace(/\s+Let me know if you need more information/gi, "\n\nLet me know if you need more information")
    .trim();
}

function renderInlineBold(text: string): ReactNode[] {
  const chunks = text.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
  return chunks.map((chunk, index) => {
    if (chunk.startsWith("**") && chunk.endsWith("**")) {
      return <strong key={`bold-${index}`}>{chunk.slice(2, -2)}</strong>;
    }
    return <Fragment key={`text-${index}`}>{chunk}</Fragment>;
  });
}

function AssistantFormattedText({ text }: { text: string }): JSX.Element {
  const normalized = normalizeAssistantText(text);
  const lines = normalized.split("\n").filter((line) => line.trim().length > 0);

  return (
    <div className="message-richtext">
      {lines.map((line, index) => {
        const trimmed = line.trim();
        const isNumbered = /^\d+\.\s/.test(trimmed);
        const isDetail = /^-\s/.test(trimmed);

        if (isNumbered) {
          return (
            <p key={`line-${index}`} className="message-richtext-item-title">
              {renderInlineBold(trimmed)}
            </p>
          );
        }

        if (isDetail) {
          return (
            <p key={`line-${index}`} className="message-richtext-item-meta">
              {renderInlineBold(trimmed.replace(/^-\s*/, ""))}
            </p>
          );
        }

        return (
          <p key={`line-${index}`} className="message-richtext-paragraph">
            {renderInlineBold(trimmed)}
          </p>
        );
      })}
    </div>
  );
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
              {message.role === "assistant" && !message.isError ? (
                <AssistantFormattedText text={message.text} />
              ) : (
                <p className="message-text">{message.text}</p>
              )}
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
