import { useState, useRef, useEffect } from "react";
import { Send, RotateCcw, TrendingUp } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { api } from "../lib/api";

function newSessionId() {
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

const SUGGESTIONS = [
  "How did HDFC Bank perform in 2023?",
  "Which sector had the highest volatility?",
  "Top performing stocks in 2024",
  "Compare IT vs Financials returns",
];

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(newSessionId());
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage(text) {
    const question = (text ?? input).trim();
    if (!question || loading) return;

    setMessages((m) => [...m, { role: "user", content: question }]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.chat(question, sessionId);
      setMessages((m) => [...m, { role: "assistant", content: res.answer }]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content:
            "I ran into a problem reaching the insights engine. " +
            (err.message?.includes("took too long")
              ? "The server may be waking up — please try again in a moment."
              : "Please try again shortly."),
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function resetConversation() {
    setMessages([]);
    setSessionId(newSessionId());
  }

  const isEmpty = messages.length === 0;

  return (
    <div className="flex-1 flex flex-col items-center px-4 md:px-6">
      <div className="w-full max-w-3xl flex-1 flex flex-col">

        {isEmpty ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center px-4">
            <TrendingUp className="w-9 h-9 text-brass mb-5" strokeWidth={1.5} />
            <h2 className="font-display text-3xl md:text-4xl font-medium text-paper mb-3">
              Ask the market anything
            </h2>
            <p className="text-slate-light max-w-md mb-8 leading-relaxed">
              Grounded in 28 years of Nifty 50 data — returns, volatility,
              sector trends, and anomalies. Every answer cites real numbers.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full max-w-lg">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  className="text-left px-4 py-3 rounded-lg border hairline bg-ink-card text-sm text-slate-light hover:text-paper hover:border-brass/40 transition-colors duration-150"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto py-8 space-y-5"
          >
            {messages.map((msg, i) => (
              <MessageBubble key={i} {...msg} />
            ))}
            {loading && <TypingIndicator />}
          </div>
        )}

        <div className="sticky bottom-0 bg-ink pt-3 pb-6">
          {!isEmpty && (
            <div className="flex justify-end mb-2">
              <button
                onClick={resetConversation}
                className="flex items-center gap-1.5 text-xs text-slate-light hover:text-brass transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                New conversation
              </button>
            </div>
          )}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              sendMessage();
            }}
            className="flex items-end gap-2 rounded-xl border hairline bg-ink-card px-3 py-2.5 focus-within:border-brass/50 transition-colors"
          >
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              placeholder="Ask about a stock, sector, or trend…"
              rows={1}
              className="flex-1 resize-none bg-transparent text-paper placeholder:text-slate-light/60 text-[15px] py-1.5 outline-none max-h-32"
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="flex items-center justify-center w-9 h-9 rounded-lg bg-brass text-ink disabled:opacity-30 disabled:cursor-not-allowed hover:bg-brass-bright transition-colors shrink-0"
            >
              <Send className="w-4 h-4" strokeWidth={2} />
            </button>
          </form>
          <p className="text-[11px] text-slate-light/60 text-center mt-2.5">
            Historical data only — not financial advice.
          </p>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ role, content, error }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] md:max-w-[75%] rounded-xl px-4 py-3 text-[15px] leading-relaxed ${
          isUser
            ? "bg-brass text-ink font-medium"
            : error
            ? "bg-brick-red/15 border border-brick-red/30 text-paper"
            : "bg-ink-card border hairline text-paper"
        }`}
      >
        {isUser ? (
          content
        ) : (
          <div className="prose-chat">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="bg-ink-card border hairline rounded-xl px-4 py-3.5 flex gap-1.5">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="w-1.5 h-1.5 rounded-full bg-brass/70 animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  );
}
