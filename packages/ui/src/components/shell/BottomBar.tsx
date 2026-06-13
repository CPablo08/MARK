import { AnimatePresence, motion } from "framer-motion";
import { useMarkStore, type PanelId } from "../../store/markStore";
import { useMarkCommand } from "../../hooks/useMarkCommand";

const PANELS: { id: PanelId; label: string }[] = [
  { id: "messages", label: "Chat" },
  { id: "ops", label: "Ops" },
  { id: "vault", label: "Vault" },
  { id: "integrations", label: "Plugins" },
  { id: "logs", label: "Logs" },
  { id: "settings", label: "Settings" },
];

export function BottomBar() {
  const openPanel = useMarkStore((s) => s.openPanel);
  const togglePanel = useMarkStore((s) => s.togglePanel);
  const voiceRecording = useMarkStore((s) => s.voiceRecording);
  const voiceSpeaking = useMarkStore((s) => s.voiceSpeaking);
  const voiceTranscript = useMarkStore((s) => s.voiceTranscript);
  const voiceError = useMarkStore((s) => s.voiceError);
  const messages = useMarkStore((s) => s.messages);
  const chatMode = useMarkStore((s) => s.chatMode);
  const wsConnected = useMarkStore((s) => s.wsConnected);
  const chatLoadingLabel = useMarkStore((s) => s.chatLoadingLabel);
  const orbState = useMarkStore((s) => s.orbState);
  const tasks = useMarkStore((s) => s.tasks);
  const activeOpsCount = tasks.filter((t) =>
    ["pending", "queued", "running", "awaiting_approval"].includes(t.status)
  ).length;

  const { sendCommand, toggleVoiceSession, voiceSessionActive } = useMarkCommand();

  const chatCount = messages.filter((m) => m.role === "user").length;

  return (
    <motion.div className="mark-bottom-bar" role="toolbar" aria-label="MARK command bar">
      <div className="mark-bottom-bar-inner">
        <nav className="mark-bottom-nav" aria-label="Panels">
          {PANELS.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => togglePanel(p.id)}
              className={`mark-bottom-tab ${openPanel === p.id ? "mark-bottom-tab--active" : ""}`}
            >
              {p.label}
              {p.id === "messages" && chatCount > 0 && (
                <span className="mark-bottom-badge">{chatCount}</span>
              )}
              {p.id === "ops" && activeOpsCount > 0 && (
                <span className="mark-bottom-badge mark-bottom-badge--ops">{activeOpsCount}</span>
              )}
            </button>
          ))}
        </nav>

        <div className="mark-bottom-command">
          <button
            type="button"
            onClick={() => toggleVoiceSession()}
            className={`mark-bottom-mic ${
              voiceSessionActive || voiceRecording ? "mark-bottom-mic--rec" : ""
            }`}
            title={voiceSessionActive ? "End voice conversation" : "Start voice conversation"}
            aria-label={voiceSessionActive ? "End voice conversation" : "Start voice conversation"}
            aria-pressed={voiceSessionActive}
          >
            <MicIcon />
          </button>
          <input
            id="mark-command-input"
            disabled={voiceRecording || voiceSpeaking}
            placeholder={
              voiceSessionActive ? "Voice conversation active…" : "Speak or type to MARK…"
            }
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                const v = (e.target as HTMLInputElement).value;
                if (v.trim()) {
                  sendCommand(v);
                  (e.target as HTMLInputElement).value = "";
                }
              }
            }}
            className="mark-bottom-input"
          />
          <button
            type="button"
            className="mark-bottom-send"
            title="Send"
            aria-label="Send"
            onClick={() => {
              const input = document.getElementById("mark-command-input") as HTMLInputElement;
              if (input?.value.trim()) {
                sendCommand(input.value);
                input.value = "";
              }
            }}
          >
            <SendIcon />
          </button>
        </div>
      </div>

      <AnimatePresence>
        {(chatLoadingLabel ||
          voiceSessionActive ||
          voiceRecording ||
          voiceSpeaking ||
          voiceTranscript ||
          voiceError ||
          !wsConnected) && (
          <motion.p
            className={`mark-bottom-status ${voiceError ? "mark-bottom-status--error" : ""}`}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
          >
            {voiceError
              ? voiceError
              : chatLoadingLabel && orbState === "thinking" && !voiceSpeaking
                ? `${chatLoadingLabel}…`
                : !wsConnected
                ? "Reconnecting live updates…"
                : voiceSpeaking
                  ? "MARK is speaking…"
                  : voiceRecording
                    ? voiceTranscript
                      ? `Listening: “${voiceTranscript.slice(0, 100)}${voiceTranscript.length > 100 ? "…" : ""}”`
                      : "Listening… speak naturally, pause when done"
                    : voiceSessionActive
                      ? "Voice conversation — tap mic to end"
                      : chatMode === "task"
                        ? "Executing task…"
                        : null}
          </motion.p>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function MicIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M12 14a3 3 0 003-3V5a3 3 0 10-6 0v6a3 3 0 003 3zm5-3a5 5 0 01-10 0H5a7 7 0 0014 0h-2zm-1 6H8v2h8v-2z" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M12 19V5M5 12l7-7 7 7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
