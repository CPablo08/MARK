import { useState } from "react";
import { motion } from "framer-motion";
import { api } from "../../lib/api";
import { useMarkStore } from "../../store/markStore";

export function ChatInput() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const token = useMarkStore((s) => s.token);
  const addMessage = useMarkStore((s) => s.addMessage);
  const setOrbState = useMarkStore((s) => s.setOrbState);

  const send = async () => {
    if (!text.trim() || !token || loading) return;
    const content = text.trim();
    setText("");
    setLoading(true);
    setOrbState("thinking");

    addMessage({ id: crypto.randomUUID(), role: "user", content });

    try {
      await api.chat(token, { content });
    } catch (e) {
      addMessage({
        id: crypto.randomUUID(),
        role: "assistant",
        content: `**Error:** ${e instanceof Error ? e.message : "Failed to send"}`,
      });
      setOrbState("idle");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto w-full">
      <motion.div className="flex gap-2 items-center" layout>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), send())}
          placeholder="Command MARK…"
          className="flex-1 bg-surface border border-border rounded-lg px-4 py-2.5 text-sm text-white placeholder:text-gray-600 focus:outline-none focus:border-accent/40 focus:ring-1 focus:ring-accent/20"
          disabled={loading}
        />
        <motion.button
          type="button"
          whileTap={{ scale: 0.97 }}
          onClick={send}
          disabled={loading || !text.trim()}
          className="px-5 py-2.5 rounded-lg bg-accent/15 text-accent border border-accent/25 text-sm font-medium hover:bg-accent/25 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? "…" : "Execute"}
        </motion.button>
      </motion.div>
    </div>
  );
}
