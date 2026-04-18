"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";

import type { ChatFare, ChatResponse, TravelChatWidgetProps } from "./types";

type UiMessage = {
  id: string;
  role: "assistant" | "user";
  text: string;
  fares?: ChatFare[];
};

const defaultLabels = {
  launcher: "Travel help",
  title: "Plan your next trip",
  subtitle: "Ask for routes, dates, or the best available fare.",
  inputPlaceholder: "Example: Cheapest JFK to JED on 2026-06-14 for 2 adults",
  submit: "Send",
  loading: "Checking live fares...",
  emptyState: "No fares returned yet.",
  intro: "Ask about flights and I will return ranked fare options from your Sabre-powered API.",
};

const widgetStyles = `
.travel-chat-widget-shell {
  --travel-chat-accent: #c96f1a;
  --travel-chat-panel-bg: linear-gradient(180deg, #fffaf1 0%, #f4ede2 100%);
  --travel-chat-border: rgba(73, 50, 24, 0.12);
  --travel-chat-text: #2b2117;
  --travel-chat-muted: #6d5a47;
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 50;
  font-family: "DM Sans", "Segoe UI", sans-serif;
  color: var(--travel-chat-text);
}

.travel-chat-widget-launcher {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  border: 0;
  border-radius: 999px;
  padding: 14px 18px;
  background: linear-gradient(135deg, var(--travel-chat-accent), #8c4b16);
  color: #fffaf4;
  box-shadow: 0 24px 50px rgba(112, 59, 17, 0.24);
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 700;
}

.travel-chat-widget-launcher-glow {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #fff5c2;
  box-shadow: 0 0 0 6px rgba(255, 245, 194, 0.18);
}

.travel-chat-widget-panel {
  width: min(380px, calc(100vw - 32px));
  margin-top: 14px;
  border: 1px solid var(--travel-chat-border);
  border-radius: 28px;
  overflow: hidden;
  background: var(--travel-chat-panel-bg);
  box-shadow: 0 30px 80px rgba(37, 24, 10, 0.18);
  backdrop-filter: blur(8px);
}

.travel-chat-widget-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 22px 22px 18px;
  background:
    radial-gradient(circle at top left, rgba(255, 245, 227, 0.95), transparent 45%),
    linear-gradient(135deg, rgba(201, 111, 26, 0.16), rgba(140, 75, 22, 0.03));
}

.travel-chat-widget-header h2 {
  margin: 4px 0 6px;
  font-size: 1.2rem;
  line-height: 1.2;
}

.travel-chat-widget-header p {
  margin: 0;
  color: var(--travel-chat-muted);
  font-size: 0.92rem;
}

.travel-chat-widget-eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--travel-chat-accent);
}

.travel-chat-widget-close {
  align-self: flex-start;
  border: 0;
  border-radius: 999px;
  padding: 10px 12px;
  background: rgba(255, 250, 241, 0.82);
  color: var(--travel-chat-text);
  cursor: pointer;
}

.travel-chat-widget-feed {
  max-height: 420px;
  overflow-y: auto;
  padding: 18px 18px 8px;
}

.travel-chat-widget-message {
  margin-bottom: 14px;
  padding: 14px 16px;
  border-radius: 20px;
  line-height: 1.5;
}

.travel-chat-widget-message p {
  margin: 0;
}

.travel-chat-widget-message-assistant {
  background: rgba(255, 250, 244, 0.94);
  border: 1px solid rgba(73, 50, 24, 0.08);
}

.travel-chat-widget-message-user {
  margin-left: 42px;
  background: linear-gradient(135deg, rgba(201, 111, 26, 0.16), rgba(140, 75, 22, 0.08));
}

.travel-chat-widget-fares {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}

.travel-chat-widget-fare-card {
  display: grid;
  gap: 4px;
  width: 100%;
  text-align: left;
  border: 1px solid rgba(201, 111, 26, 0.16);
  border-radius: 18px;
  padding: 12px 14px;
  background: linear-gradient(180deg, rgba(255, 247, 238, 0.98), rgba(255, 255, 255, 0.88));
  color: var(--travel-chat-text);
  cursor: pointer;
}

.travel-chat-widget-fare-card strong {
  font-size: 1rem;
}

.travel-chat-widget-fare-topline {
  color: var(--travel-chat-muted);
  font-size: 0.82rem;
}

.travel-chat-widget-loading {
  margin: 8px 0 12px;
  color: var(--travel-chat-muted);
  font-size: 0.9rem;
}

.travel-chat-widget-form {
  padding: 14px 18px 18px;
  border-top: 1px solid rgba(73, 50, 24, 0.08);
  background: rgba(255, 250, 241, 0.7);
}

.travel-chat-widget-form textarea {
  width: 100%;
  resize: none;
  border: 1px solid rgba(73, 50, 24, 0.12);
  border-radius: 18px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.82);
  color: var(--travel-chat-text);
  font: inherit;
}

.travel-chat-widget-form textarea:focus {
  outline: 2px solid rgba(201, 111, 26, 0.18);
  border-color: rgba(201, 111, 26, 0.35);
}

.travel-chat-widget-actions {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  margin-top: 12px;
}

.travel-chat-widget-actions span {
  color: var(--travel-chat-muted);
  font-size: 0.82rem;
}

.travel-chat-widget-actions button {
  border: 0;
  border-radius: 999px;
  padding: 11px 16px;
  background: var(--travel-chat-text);
  color: #fff8f2;
  cursor: pointer;
  font-weight: 700;
}

.travel-chat-widget-actions button:disabled {
  cursor: not-allowed;
  opacity: 0.48;
}

@media (max-width: 640px) {
  .travel-chat-widget-shell {
    right: 12px;
    left: 12px;
    bottom: 12px;
  }

  .travel-chat-widget-launcher {
    width: 100%;
    justify-content: center;
  }

  .travel-chat-widget-panel {
    width: 100%;
  }
}
`;

function createId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  return `travel-chat-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function TravelChatWidget({
  apiBaseUrl,
  className,
  accentColor = "#c96f1a",
  greeting,
  labels,
  defaultOpen = false,
  maxVisibleFares = 3,
  onFareSelect,
}: TravelChatWidgetProps) {
  const mergedLabels = { ...defaultLabels, ...labels };
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<UiMessage[]>([
    {
      id: "intro",
      role: "assistant",
      text: greeting ?? mergedLabels.intro,
    },
  ]);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedMessage = inputValue.trim();
    if (!trimmedMessage || isLoading) {
      return;
    }

    const userMessage: UiMessage = {
      id: createId(),
      role: "user",
      text: trimmedMessage,
    };

    setMessages((current) => [...current, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: trimmedMessage }),
      });

      if (!response.ok) {
        throw new Error(`Widget request failed with status ${response.status}`);
      }

      const data = (await response.json()) as ChatResponse;
      const assistantMessage: UiMessage = {
        id: createId(),
        role: "assistant",
        text: data.answer,
        fares: data.fares.slice(0, maxVisibleFares),
      };

      setMessages((current) => [...current, assistantMessage]);
    } catch (error) {
      const fallbackText = error instanceof Error ? error.message : "Unable to reach the travel assistant.";
      setMessages((current) => [
        ...current,
        {
          id: createId(),
          role: "assistant",
          text: `I could not complete the request. ${fallbackText}`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div
      className={`travel-chat-widget-shell${className ? ` ${className}` : ""}`}
      style={{ ["--travel-chat-accent" as string]: accentColor }}
    >
      <style>{widgetStyles}</style>
      <button
        type="button"
        className="travel-chat-widget-launcher"
        aria-expanded={isOpen}
        onClick={() => setIsOpen((current) => !current)}
      >
        <span className="travel-chat-widget-launcher-glow" />
        <span>{mergedLabels.launcher}</span>
      </button>

      {isOpen ? (
        <section className="travel-chat-widget-panel" aria-label="Travel booking assistant">
          <header className="travel-chat-widget-header">
            <div>
              <p className="travel-chat-widget-eyebrow">Live fare assistant</p>
              <h2>{mergedLabels.title}</h2>
              <p>{mergedLabels.subtitle}</p>
            </div>
            <button
              type="button"
              className="travel-chat-widget-close"
              aria-label="Close travel assistant"
              onClick={() => setIsOpen(false)}
            >
              Close
            </button>
          </header>

          <div className="travel-chat-widget-feed" ref={scrollRef}>
            {messages.map((message) => (
              <article
                key={message.id}
                className={`travel-chat-widget-message travel-chat-widget-message-${message.role}`}
              >
                <p>{message.text}</p>
                {message.fares && message.fares.length > 0 ? (
                  <div className="travel-chat-widget-fares">
                    {message.fares.map((fare) => (
                      <button
                        key={fare.raw_offer_id ?? `${message.id}-${fare.rank}`}
                        type="button"
                        className="travel-chat-widget-fare-card"
                        onClick={() => onFareSelect?.(fare)}
                      >
                        <span className="travel-chat-widget-fare-topline">
                          Option {fare.rank} · {fare.validating_carrier ?? "Airline pending"}
                        </span>
                        <strong>
                          {fare.total_price.toFixed(2)} {fare.currency}
                        </strong>
                        <span>
                          {fare.departure_airport ?? "Origin"} to {fare.arrival_airport ?? "Destination"}
                        </span>
                        <span>
                          {fare.number_of_stops === 0
                            ? "Non-stop"
                            : `${fare.number_of_stops ?? "Unknown"} stop(s)`}
                        </span>
                      </button>
                    ))}
                  </div>
                ) : null}
              </article>
            ))}

            {isLoading ? <p className="travel-chat-widget-loading">{mergedLabels.loading}</p> : null}
          </div>

          <form className="travel-chat-widget-form" onSubmit={handleSubmit}>
            <textarea
              name="message"
              rows={3}
              value={inputValue}
              onChange={(event) => setInputValue(event.target.value)}
              placeholder={mergedLabels.inputPlaceholder}
            />
            <div className="travel-chat-widget-actions">
              <span>{mergedLabels.emptyState}</span>
              <button type="submit" disabled={isLoading || inputValue.trim().length === 0}>
                {mergedLabels.submit}
              </button>
            </div>
          </form>
        </section>
      ) : null}
    </div>
  );
}
