import { motion } from "framer-motion";
import { useMarkStore } from "../../store/markStore";

export function CollapsedChatDock() {
  const workspaceMode = useMarkStore((s) => s.workspaceMode);
  const messages = useMarkStore((s) => s.messages);
  const chatLoadingLabel = useMarkStore((s) => s.chatLoadingLabel);
  const setOpenPanel = useMarkStore((s) => s.setOpenPanel);
  const setShowMessages = useMarkStore((s) => s.setShowMessages);

  if (workspaceMode === "idle") return null;

  const recent = messages.filter((m) => m.content.trim()).slice(-4);

  return (
    <motion.div
      className="mark-collapsed-chat"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 12 }}
    >
      <div className="mark-collapsed-chat__header">
        <span className="text-[9px] uppercase tracking-widest text-muted">
          Conversation
        </span>
        <span className="text-[10px] text-muted">Type below to talk</span>
      </div>
      <ul className="mark-collapsed-chat__list">
        {chatLoadingLabel && (
          <li className="mark-collapsed-chat__line mark-collapsed-chat__line--loading">
            <span className="mark-collapsed-chat__role">MARK</span>
            <span className="truncate">{chatLoadingLabel}…</span>
          </li>
        )}
        {recent.length === 0 && !chatLoadingLabel ? (
          <li className="text-[11px] text-muted">No messages yet — use the bar below.</li>
        ) : (
          recent.map((m) => (
            <li key={m.id} className="mark-collapsed-chat__line">
              <span className="mark-collapsed-chat__role">
                {m.role === "user" ? "You" : "MARK"}
              </span>
              <span className="truncate">{m.content.replace(/\n+/g, " ").slice(0, 120)}</span>
            </li>
          ))
        )}
      </ul>
    </motion.div>
  );
}
