"use client";

import { useEffect, useMemo, useState } from "react";

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
  text: "Welcome to ShopPilot. Ask for recommendations, upload an image, or combine both for more relevant results.",
};

export function ChatContainer(): JSX.Element {
  const [messages, setMessages] = useState<ChatMessage[]>([initialAssistantMessage]);
  const [isLoading, setIsLoading] = useState(false);
  const [isAssistantTyping, setIsAssistantTyping] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showStarters, setShowStarters] = useState(true);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const sessionId = useMemo(() => generateClientId("session"), []);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const savedTheme = window.localStorage.getItem("shoppilot-theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const resolvedTheme = savedTheme === "dark" || (!savedTheme && prefersDark) ? "dark" : "light";

    setTheme(resolvedTheme);
    document.documentElement.setAttribute("data-theme", resolvedTheme);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    document.documentElement.setAttribute("data-theme", theme);
    window.localStorage.setItem("shoppilot-theme", theme);
  }, [theme]);

  const sleep = (ms: number): Promise<void> =>
    new Promise((resolve) => {
      window.setTimeout(resolve, ms);
    });

  const typeAssistantMessage = async (
    messageId: string,
    fullText: string,
    intent: ChatMessage["intent"],
    products: ChatMessage["products"]
  ): Promise<void> => {
    const length = fullText.length;
    const step = length > 260 ? 2 : 1;

    const getDelayMs = (char: string): number => {
      if (char === "." || char === "!" || char === "?") {
        return 72;
      }
      if (char === "," || char === ";" || char === ":") {
        return 46;
      }
      if (char === "\n") {
        return 58;
      }
      return 20;
    };

    setIsAssistantTyping(true);
    for (let index = step; index <= length; index += step) {
      const nextText = fullText.slice(0, index);
      setMessages((prev) =>
        prev.map((message) =>
          message.id === messageId
            ? {
                ...message,
                text: nextText,
              }
            : message
        )
      );

      const lastChar = fullText.charAt(index - 1);
      await sleep(getDelayMs(lastChar));
    }

    setMessages((prev) =>
      prev.map((message) =>
        message.id === messageId
          ? {
              ...message,
              text: fullText,
              intent,
              products,
            }
          : message
      )
    );
    setIsAssistantTyping(false);
  };

  const handleSend = async (payload: {
    message?: string;
    imageFile?: File | null;
  }): Promise<void> => {
    console.log("[frontend.chat] handleSend:start", {
      message: payload.message?.slice(0, 120) ?? "",
      hasImage: Boolean(payload.imageFile),
    });
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
        text: "",
        intent: assistantResponse.intent,
        products: [],
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setIsLoading(false);
      await typeAssistantMessage(
        assistantMessage.id,
        assistantResponse.response_text,
        assistantResponse.intent,
        assistantResponse.products
      );
      console.log("[frontend.chat] handleSend:assistant_received", {
        intent: assistantResponse.intent,
        products: assistantResponse.products?.length ?? 0,
      });
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
      console.log("[frontend.chat] handleSend:error", {
        message: fallbackErrorMessage,
      });
    } finally {
      setIsLoading(false);
      setSelectedFile(null);
      console.log("[frontend.chat] handleSend:done");
    }
  };

  return (
    <main className="chat-page">
      <section className="app-shell">
        <aside className="app-sidebar">
          <div className="theme-switch-row">
            <span>{theme === "dark" ? "Night mode" : "Day mode"}</span>
            <label className="theme-switch" htmlFor="theme-switch-input">
              <input
                checked={theme === "dark"}
                id="theme-switch-input"
                onChange={(event) => setTheme(event.target.checked ? "dark" : "light")}
                type="checkbox"
              />
              <span className="theme-switch-track" aria-hidden="true">
                <span className="theme-switch-icon theme-switch-icon-sun">☀</span>
                <span className="theme-switch-icon theme-switch-icon-moon">🌙</span>
                <span className="theme-switch-thumb" />
              </span>
            </label>
          </div>

          <div className="brand-row">
            <div className="brand-avatar" aria-hidden="true">
              <div className="brand-avatar-core" />
              <div className="brand-avatar-glow" />
            </div>
            <div>
              <p className="chat-eyebrow">Multimodal Shopping Assistant</p>
              <h1>ShopPilot</h1>
            </div>
          </div>

          <p className="sidebar-subtitle">
            Unified chat, text recommendation, image search, and hybrid product discovery.
          </p>

          <div className="chat-use-cases" aria-label="Primary use cases">
            <span>Text Recommendations</span>
            <span>Image Search</span>
            <span>Hybrid Results</span>
          </div>

          <section className="chat-starters" aria-label="Starter prompts">
            <button
              className="chat-starters-toggle"
              onClick={() => setShowStarters((value) => !value)}
              type="button"
            >
              <span>{showStarters ? "▾" : "▸"}</span>
              <span>Starter prompts</span>
            </button>
            {showStarters ? (
              <ul>
                <li>"Recommend sneakers for daily wear"</li>
                <li>"Show me watches under $65"</li>
                <li>Upload a product photo and add "find similar but cheaper"</li>
              </ul>
            ) : null}
          </section>
        </aside>

        <section className="chat-panel">
          <header className="chat-panel-header">
            <p>Assistant</p>
            <span>Single unified endpoint</span>
          </header>

          {errorMessage ? <ErrorBanner message={errorMessage} onDismiss={() => setErrorMessage(null)} /> : null}

          <MessageList messages={messages} onImageDropped={setSelectedFile} />

          <footer className="chat-footer">
            {isLoading || isAssistantTyping ? (
              <div className="loading-inline">
                <LoadingSpinner />
                <span>{isLoading ? "Thinking..." : "Typing..."}</span>
              </div>
            ) : null}
            <MessageInput
              isLoading={isLoading || isAssistantTyping}
              selectedFile={selectedFile}
              onFileSelected={setSelectedFile}
              onSubmit={handleSend}
            />
          </footer>
        </section>
      </section>
    </main>
  );
}
