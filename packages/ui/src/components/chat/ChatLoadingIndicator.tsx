/** Animated loading line for in-progress assistant replies. */
export function ChatLoadingIndicator({ label = "Thinking" }: { label?: string }) {
  return (
    <span className="mark-chat-loading" aria-live="polite" aria-busy="true">
      <span className="mark-chat-loading__text">{label}</span>
      <span className="mark-chat-loading__dots" aria-hidden>
        <span>.</span>
        <span>.</span>
        <span>.</span>
      </span>
    </span>
  );
}

export function isAssistantLoading(m: {
  role: string;
  streaming?: boolean;
  content: string;
}): boolean {
  return (
    m.role === "assistant" &&
    !!m.streaming &&
    (!m.content.trim() || m.content.startsWith("…") || m.content.endsWith("…"))
  );
}
