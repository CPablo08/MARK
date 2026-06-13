import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { useMarkStore } from "../../store/markStore";

export function ChatHistoryPanel() {
  const token = useMarkStore((s) => s.token);
  const sessionId = useMarkStore((s) => s.sessionId);
  const setMessages = useMarkStore((s) => s.setMessages);
  const setSessionId = useMarkStore((s) => s.setSessionId);
  const setOpenPanel = useMarkStore((s) => s.setOpenPanel);

  const { data, isLoading, error } = useQuery({
    queryKey: ["sessions", token],
    queryFn: () => api.sessions(token!),
    enabled: !!token,
  });

  const openSession = async (id: string) => {
    if (!token) return;
    const msgs = await api.sessionMessages(token, id);
    setSessionId(id);
    localStorage.setItem("mark_session_id", id);
    setMessages(
      msgs.map((m) => ({
        id: m.id,
        role: m.role as "user" | "assistant",
        content: m.content,
      }))
    );
    useMarkStore.getState().setShowMessages(true);
    setOpenPanel("messages");
  };

  if (isLoading) return <p className="text-sm text-muted">Loading chat history…</p>;
  if (error) return <p className="text-sm text-red-400">{error.message}</p>;
  if (!data?.length) {
    return (
      <p className="text-sm text-muted">
        No saved chats yet. Messages are stored automatically when you talk to MARK.
      </p>
    );
  }

  return (
    <ul className="space-y-1.5 max-h-[min(50vh,400px)] overflow-y-auto">
      {data.map((s) => (
        <li key={s.id}>
          <button
            type="button"
            onClick={() => void openSession(s.id)}
            className={`w-full text-left px-3 py-2.5 rounded-lg border transition-colors ${
              sessionId === s.id
                ? "border-accent/40 bg-accent/10"
                : "border-border/60 bg-surface/50 hover:border-border"
            }`}
          >
            <p className="text-sm text-gray-200 truncate">{s.title || "Untitled chat"}</p>
            <p className="text-[10px] text-muted mt-0.5">
              {s.message_count} messages · {new Date(s.updated_at).toLocaleString()}
            </p>
          </button>
        </li>
      ))}
    </ul>
  );
}
