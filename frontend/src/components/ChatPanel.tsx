import { useEffect, useRef, useState } from "react";
import type { Message } from "../types";

interface Props {
  messages: Message[];
  onSend: (content: string) => Promise<void>;
  onStop: () => void;
  loading: boolean;
  error: string | null;
}

export default function ChatPanel({ messages, onSend, onStop, loading, error }: Props) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Auto-resize the textarea to fit its content, capped at 200px.
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [input]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    await onSend(text);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="flex h-full flex-col">
      <main className="flex-1 overflow-y-auto px-6 py-4">
        <div className="mx-auto flex max-w-2xl flex-col gap-3">
          {messages.map((m) => (
            <div
              key={m.id}
              dir="auto"
              className={`whitespace-pre-wrap rounded-lg px-4 py-2 text-sm ${
                m.role === "user"
                  ? "ml-auto max-w-[80%] bg-brand-orange text-white"
                  : "mr-auto max-w-[80%] bg-brand-white text-gray-800 shadow-sm"
              }`}
            >
              {m.content}
            </div>
          ))}
          {loading && (
            <div className="mr-auto flex items-center gap-2 text-sm text-gray-400">
              <span>Thinking…</span>
              <button
                onClick={onStop}
                className="rounded border border-gray-300 px-2 py-0.5 text-xs text-gray-500 hover:bg-gray-50"
              >
                Stop
              </button>
            </div>
          )}
          {error && <div className="mr-auto text-sm text-red-500">{error}</div>}
          <div ref={bottomRef} />
        </div>
      </main>

      <footer className="border-t bg-brand-white px-6 py-4">
        <div className="mx-auto flex max-w-2xl items-end gap-2">
          <textarea
            ref={textareaRef}
            rows={1}
            className="max-h-[200px] flex-1 resize-none overflow-y-auto rounded-lg border px-3 py-2 text-sm outline-none focus:border-brand-orange"
            placeholder="Type a message… (Enter to send, Shift+Enter for a new line)"
            dir="auto"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            className="rounded-lg bg-brand-orange hover:bg-brand-orange-dark px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            onClick={handleSend}
            disabled={loading}
          >
            Send
          </button>
        </div>
      </footer>
    </div>
  );
}
