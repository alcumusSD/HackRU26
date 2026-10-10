"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { postChat } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

type Props = {
  context: Record<string, unknown>;
};

export function RadarChat({ context }: Props) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, open, busy]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || busy) return;

    const nextHistory = [...messages, { role: "user" as const, content: text }];
    setMessages(nextHistory);
    setInput("");
    setBusy(true);
    setError(null);

    try {
      const res = await postChat({
        message: text,
        context,
        history: messages,
      });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.reply },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chat failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={`radar-chat ${open ? "radar-chat--open" : ""}`}>
      {!open ? (
        <button
          type="button"
          className="radar-chat-toggle"
          onClick={() => setOpen(true)}
          aria-expanded={false}
        >
          Ask about this view
        </button>
      ) : (
        <section className="radar-chat-panel" aria-label="Evidence Radar chat">
          <header className="radar-chat-head">
            <div>
              <p className="eyebrow">Assistant</p>
              <strong>Ask about what’s on screen</strong>
            </div>
            <button
              type="button"
              className="close-btn"
              onClick={() => setOpen(false)}
            >
              Close
            </button>
          </header>
          <p className="radar-chat-note">
            Answers use only the current Map/Network selection and scores — not
            medical advice.
          </p>
          <div className="radar-chat-messages" ref={listRef}>
            {messages.length === 0 && (
              <p className="muted">
                Try: “Why is this gene Validated?” or “How many Phase 3 trials?”
              </p>
            )}
            {messages.map((m, i) => (
              <div
                key={`${m.role}-${i}`}
                className={`radar-chat-bubble radar-chat-bubble--${m.role}`}
              >
                {m.content}
              </div>
            ))}
            {busy && <p className="muted">Thinking…</p>}
            {error && <p className="error">{error}</p>}
          </div>
          <form className="radar-chat-form" onSubmit={onSubmit}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about scores, trials, or this selection…"
              aria-label="Chat message"
              disabled={busy}
              autoComplete="off"
            />
            <button type="submit" disabled={busy || !input.trim()}>
              Send
            </button>
          </form>
        </section>
      )}
    </div>
  );
}
