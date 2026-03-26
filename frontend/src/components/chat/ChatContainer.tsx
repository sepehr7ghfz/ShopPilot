"use client";

import { DragEvent, useEffect, useMemo, useState } from "react";

import { MessageInput } from "@/components/chat/MessageInput";
import { MessageList } from "@/components/chat/MessageList";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { sendAssistantMessage } from "@/lib/api";
import { ChatMessage, Product } from "@/lib/types";
import { formatPrice } from "@/lib/utils";
import { generateClientId } from "@/lib/utils";
import { resolveProductImage } from "@/lib/utils";

const initialAssistantMessage: ChatMessage = {
  id: "assistant-welcome",
  role: "assistant",
  text: "Welcome to ShopPilot. Ask for recommendations, upload an image, or combine both for more relevant results.",
};

interface CartLine {
  product: Product;
  quantity: number;
}

export function ChatContainer(): JSX.Element {
  const [messages, setMessages] = useState<ChatMessage[]>([initialAssistantMessage]);
  const [isLoading, setIsLoading] = useState(false);
  const [isAssistantTyping, setIsAssistantTyping] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showStarters, setShowStarters] = useState(true);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [cartItems, setCartItems] = useState<CartLine[]>([]);
  const [cartMinimized, setCartMinimized] = useState(false);

  const sessionId = useMemo(() => generateClientId("session"), []);

  const cartQuantity = useMemo(
    () => cartItems.reduce((sum, line) => sum + line.quantity, 0),
    [cartItems]
  );

  const cartTotal = useMemo(
    () => cartItems.reduce((sum, line) => sum + line.product.price * line.quantity, 0),
    [cartItems]
  );

  const addToCart = (product: Product): void => {
    setCartItems((prev) => {
      const existing = prev.find((line) => line.product.id === product.id);
      if (!existing) {
        return [...prev, { product, quantity: 1 }];
      }

      return prev.map((line) =>
        line.product.id === product.id ? { ...line, quantity: line.quantity + 1 } : line
      );
    });
  };

  const decrementCartItem = (productId: string): void => {
    setCartItems((prev) => {
      const next = prev
        .map((line) =>
          line.product.id === productId ? { ...line, quantity: line.quantity - 1 } : line
        )
        .filter((line) => line.quantity > 0);

      return next;
    });
  };

  const removeCartItem = (productId: string): void => {
    setCartItems((prev) => prev.filter((line) => line.product.id !== productId));
  };

  const handleFileDrop = (event: DragEvent<HTMLElement>): void => {
    event.preventDefault();
    const file = event.dataTransfer.files?.[0] ?? null;
    if (!file || !file.type.startsWith("image/")) {
      return;
    }
    setSelectedFile(file);
  };

  const handleDragOver = (event: DragEvent<HTMLElement>): void => {
    event.preventDefault();
  };

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

      if (assistantResponse.cart_actions?.length) {
        setCartItems((prev) => {
          const next = [...prev];
          const productsById = new Map((assistantResponse.products ?? []).map((product) => [product.id, product]));

          for (const action of assistantResponse.cart_actions ?? []) {
            if (action.action === "clear") {
              next.length = 0;
              continue;
            }

            if (action.action === "remove") {
              for (const id of action.product_ids) {
                const index = next.findIndex((item) => item.product.id === id);
                if (index >= 0) {
                  const updated = { ...next[index], quantity: next[index].quantity - 1 };
                  if (updated.quantity <= 0) {
                    next.splice(index, 1);
                  } else {
                    next[index] = updated;
                  }
                }
              }
              continue;
            }

            if (action.action === "add") {
              for (const id of action.product_ids) {
                const product = productsById.get(id);
                if (!product) {
                  continue;
                }
                const existing = next.find((item) => item.product.id === product.id);
                if (!existing) {
                  next.push({ product, quantity: 1 });
                } else {
                  existing.quantity += 1;
                }
              }
            }
          }

          return next;
        });
      }
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
    <main className="chat-page" onDrop={handleFileDrop} onDragOver={handleDragOver}>
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
              <div className="pilot-avatar">
                <div className="pilot-hat">
                  <span className="pilot-hat-badge">★</span>
                </div>
                <div className="pilot-face">
                  <span className="pilot-eye pilot-eye-left" />
                  <span className="pilot-eye pilot-eye-right" />
                  <span className="pilot-smile">◡</span>
                </div>
              </div>
            </div>
            <div className="brand-title-block">
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
                <li>Upload a photo and add "find similar items, but in a different color"</li>
                <li>"Add sneaker 1 to my shopping cart"</li>
              </ul>
            ) : null}
          </section>

          <section className="cart-panel" aria-label="Shopping cart">
            <button
              className="cart-panel-toggle"
              type="button"
              onClick={() => setCartMinimized((value) => !value)}
            >
              <span>{cartMinimized ? "▸" : "▾"}</span>
              <span>Shopping Cart</span>
              <span className="cart-panel-count">{cartQuantity}</span>
            </button>

            {!cartMinimized ? (
              cartItems.length ? (
                <>
                  <div className="cart-panel-list">
                    {cartItems.map((item) => (
                      <div key={item.product.id} className="cart-panel-item">
                        <img
                          src={resolveProductImage(item.product)}
                          alt={item.product.name}
                          className="cart-panel-item-image"
                        />
                        <div className="cart-panel-item-details">
                          <p>{item.product.name}</p>
                          <small>{formatPrice(item.product.price)}</small>
                        </div>
                        <div className="cart-panel-item-actions">
                          <button
                            type="button"
                            className="cart-qty-btn"
                            onClick={() => decrementCartItem(item.product.id)}
                            aria-label={`Decrease quantity for ${item.product.name}`}
                            title="Decrease"
                          >
                            -
                          </button>
                          <span className="cart-qty-value">{item.quantity}</span>
                          <button
                            type="button"
                            className="cart-qty-btn"
                            onClick={() => addToCart(item.product)}
                            aria-label={`Increase quantity for ${item.product.name}`}
                            title="Increase"
                          >
                            +
                          </button>
                          <button
                            type="button"
                            className="cart-remove-btn"
                            onClick={() => removeCartItem(item.product.id)}
                            aria-label={`Remove ${item.product.name} from cart`}
                            title="Remove"
                          >
                            🗑
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="cart-panel-summary">
                    <p>
                      <span>Total</span>
                      <strong>{formatPrice(cartTotal)}</strong>
                    </p>
                  </div>
                </>
              ) : (
                <p className="cart-panel-empty">Cart is empty.</p>
              )
            ) : null}
          </section>

          <div className="sidebar-checkout-dock">
            <button
              type="button"
              className={`cart-checkout-btn ${cartQuantity > 0 ? "is-active" : ""}`}
              disabled={cartQuantity === 0}
            >
              Proceed to checkout
            </button>
          </div>
        </aside>

        <section className="chat-panel">
          <header className="chat-panel-header">
            <p>Assistant</p>
            <span>Single unified endpoint</span>
          </header>

          {errorMessage ? <ErrorBanner message={errorMessage} onDismiss={() => setErrorMessage(null)} /> : null}

          <MessageList
            messages={messages}
            onAddToCart={addToCart}
          />

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
