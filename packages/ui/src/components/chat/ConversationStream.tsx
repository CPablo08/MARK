import ReactMarkdown from "react-markdown";
import { motion } from "framer-motion";
import type { ChatMessage } from "../../store/markStore";
import { useMarkStore } from "../../store/markStore";
import { ChatLoadingIndicator, isAssistantLoading } from "./ChatLoadingIndicator";

export function ConversationStream({ messages }: { messages: ChatMessage[] }) {
  const highlightMessageId = useMarkStore((s) => s.highlightMessageId);
  const chatLoadingLabel = useMarkStore((s) => s.chatLoadingLabel);
  return (
    <motion.div className="flex-1 overflow-y-auto px-6 py-4 space-y-3 min-h-0">
      {messages.length === 0 && (
        <div className="text-center mt-12 max-w-sm mx-auto">
          <p className="text-gray-500 text-sm leading-relaxed">
            Issue a command. MARK will plan, delegate, and execute autonomously.
          </p>
        </div>
      )}
      {messages.map((m) => {
        const highlighted = m.id === highlightMessageId;
        return (
        <motion.div
          key={m.id}
          id={`mark-msg-${m.id}`}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className={`max-w-xl ${m.role === "user" ? "ml-auto" : "mr-auto"}`}
        >
          <motion.div
            className={`rounded-lg px-4 py-3 text-[13px] leading-relaxed ${
              m.role === "user"
                ? "bg-accent/[0.08] border border-accent/20 text-gray-100"
                : highlighted
                  ? "bg-accent/15 border border-accent/50 text-gray-100 ring-1 ring-accent/30"
                  : "bg-surface/80 border border-border/80 text-gray-300"
            }`}
          >
            {m.role === "assistant" ? (
              <div className="prose prose-invert prose-sm max-w-none prose-p:my-1 prose-headings:text-gray-200">
                {isAssistantLoading(m) ? (
                  <ChatLoadingIndicator label={chatLoadingLabel ?? "Thinking"} />
                ) : (
                  <>
                    <ReactMarkdown>{m.content}</ReactMarkdown>
                    {m.streaming && (
                      <span className="inline-block w-1.5 h-3.5 bg-accent/80 animate-pulse ml-0.5 align-middle" />
                    )}
                  </>
                )}
              </div>
            ) : (
              m.content
            )}
          </motion.div>
        </motion.div>
      );
      })}
    </motion.div>
  );
}
