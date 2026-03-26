import { ProductGrid } from "@/components/product/ProductGrid";
import { ChatMessage } from "@/lib/types";

interface MessageListProps {
  messages: ChatMessage[];
}

export function MessageList({ messages }: MessageListProps): JSX.Element {
  return (
    <div className="message-list" aria-live="polite">
      {messages.map((message) => (
        <article
          key={message.id}
          className={`message message-${message.role} ${message.isError ? "message-error" : ""}`}
        >
          <header className="message-header">
            <span>{message.role === "user" ? "You" : "ShopPilot"}</span>
            {message.intent ? <small>{message.intent}</small> : null}
          </header>
          <p className="message-text">{message.text}</p>
          {message.imagePreviewUrl ? (
            <div className="message-image-preview-wrap">
              <img src={message.imagePreviewUrl} alt="Uploaded by user" className="message-image-preview" />
            </div>
          ) : null}
          {message.products && message.products.length > 0 ? <ProductGrid products={message.products} /> : null}
        </article>
      ))}
    </div>
  );
}
