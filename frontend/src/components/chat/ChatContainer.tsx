"use client";

import { useMemo, useState } from "react";

import { MessageInput } from "@/components/chat/MessageInput";
import { MessageList } from "@/components/chat/MessageList";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { sendAssistantMessage } from "@/lib/api";
import { ChatMessage } from "@/lib/types";
import { generateClientId } from "@/lib/utils";

const initialAssistantMessage: ChatMessage = {
  id: "assistant-welcome",
  role: "assistant",
  text: "Hi, I am ShopPilot. Ask for product recommendations, upload an image, or do both together.",
};

export function ChatContainer(): JSX.Element {
  const [messages, setMessages] = useState<ChatMessage[]>([initialAssistantMessage]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const sessionId = useMemo(() => generateClientId("session"), []);

  const handleSend = async (payload: {
    message?: string;
    imageFile?: File | null;
  }): Promise<void> => {
    const imagePreviewUrl = payload.imageFile ? URL.createObjectURL(payload.imageFile) : undefined;

    const userMessage: ChatMessage = {
      id: generateClientId("user"),
      role: "user",
      text: payload.message || (payload.imageFile ? "[Image uploaded]" : ""),
      imagePreviewUrl,
    };

    setMessages((prev) => [...prev, userMessage]);
    setErrorMessage(null);
    setIsLoading(true);

    try {
      const assistantResponse = await sendAssistantMessage({
        message: payload.message,
        imageFile: payload.imageFile,
        sessionId,
      });

      const assistantMessage: ChatMessage = {
        id: generateClientId("assistant"),
        role: "assistant",
        text: assistantResponse.response_text,
        intent: assistantResponse.intent,
        products: assistantResponse.products,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const fallbackErrorMessage =
        error instanceof Error ? error.message : "Request failed. Please check backend availability and retry.";

      setErrorMessage(fallbackErrorMessage);
      setMessages((prev) => [
        ...prev,
        {
          id: generateClientId("assistant-error"),
          role: "assistant",
          text: fallbackErrorMessage,
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="chat-page">
      <section className="chat-shell">
        <header className="chat-header">
          <h1>ShopPilot</h1>
          <p>Unified shopping assistant for chat, text recommendations, and image search.</p>
        </header>

        {errorMessage ? <ErrorBanner message={errorMessage} onDismiss={() => setErrorMessage(null)} /> : null}

        <MessageList messages={messages} />

        <footer className="chat-footer">
          {isLoading ? (
            <div className="loading-inline">
              <LoadingSpinner />
              <span>Thinking through your request...</span>
            </div>
          ) : null}
          <MessageInput isLoading={isLoading} onSubmit={handleSend} />
        </footer>
      </section>
    </main>
  );
}
