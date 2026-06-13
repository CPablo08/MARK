import { useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "../../lib/api";
import { useMarkStore } from "../../store/markStore";
import { useVoice } from "../../hooks/useVoice";
import { useAudioPlayer } from "../../hooks/useAudioPlayer";

export function CommandDock() {
  const token = useMarkStore((s) => s.token);
  const messages = useMarkStore((s) => s.messages);
  const sessionId = useMarkStore((s) => s.sessionId);
  const setSessionId = useMarkStore((s) => s.setSessionId);
  const voiceEnabled = useMarkStore((s) => s.voiceEnabled);
  const voiceRecording = useMarkStore((s) => s.voiceRecording);
  const voiceSpeaking = useMarkStore((s) => s.voiceSpeaking);
  const showMessages = useMarkStore((s) => s.showMessages);
  const setVoiceEnabled = useMarkStore((s) => s.setVoiceEnabled);
  const setShowMessages = useMarkStore((s) => s.setShowMessages);
  const setActiveNav = useMarkStore((s) => s.setActiveNav);
  const addMessage = useMarkStore((s) => s.addMessage);
  const setOrbState = useMarkStore((s) => s.setOrbState);

  const sendCommand = useCallback(
    async (content: string) => {
      if (!content.trim() || !token) return;
      addMessage({ id: crypto.randomUUID(), role: "user", content: content.trim() });
      setOrbState("thinking");
      setShowMessages(true);
      try {
        const res = await api.chat(token, {
          content: content.trim(),
          session_id: sessionId ?? undefined,
        });
        if (res.session_id) setSessionId(res.session_id);
      } catch (e) {
        addMessage({
          id: crypto.randomUUID(),
          role: "assistant",
          content: `**Error:** ${e instanceof Error ? e.message : "Failed"}`,
        });
        setOrbState("idle");
      }
    },
    [token, sessionId, addMessage, setOrbState, setSessionId, setShowMessages]
  );

  const { start, stop, cancel } = useVoice(sendCommand);
  const { playChunk, stop: stopAudio } = useAudioPlayer();

  useEffect(() => {
    const onAudio = (e: Event) => {
      const d = (e as CustomEvent).detail as { chunk: string; format: string; done?: boolean };
      if (!voiceEnabled) return;
      if (d.done) {
        useMarkStore.getState().setVoiceSpeaking(false);
        return;
      }
      if (d.chunk) {
        useMarkStore.getState().setVoiceSpeaking(true);
        playChunk(d.chunk, d.format || "mp3");
      }
    };
    const onAssistant = async (e: Event) => {
      const content = (e as CustomEvent).detail?.content as string;
      if (!voiceEnabled || !token || !content?.trim()) return;
      const plain = content.replace(/[#*_`>\[\]]/g, "").slice(0, 500);
      try {
        useMarkStore.getState().setVoiceSpeaking(true);
        const res = await api.voice.speak(token, plain);
        if (res.audio) {
          playChunk(res.audio, res.format || "mp3", () =>
            useMarkStore.getState().setVoiceSpeaking(false)
          );
        } else if (!useMarkStore.getState().wsConnected) {
          useMarkStore.getState().setVoiceSpeaking(false);
        }
      } catch {
        useMarkStore.getState().setVoiceSpeaking(false);
      }
    };
    window.addEventListener("mark:voice-audio", onAudio);
    window.addEventListener("mark:assistant-message", onAssistant);
    return () => {
      window.removeEventListener("mark:voice-audio", onAudio);
      window.removeEventListener("mark:assistant-message", onAssistant);
    };
  }, [voiceEnabled, token, playChunk]);

  const chatCount = Math.max(1, Math.ceil(messages.filter((m) => m.role === "user").length));

  return (
    <div className="mark-command-dock">
      <div className="mark-dock-inner">
        <div className="mark-dock-nav">
          <DockIcon active title="Home" onClick={() => setActiveNav("home")}>
            ⊞
          </DockIcon>
          <DockIcon title="Tasks" onClick={() => setActiveNav("tasks")}>
            ▤
          </DockIcon>
          <DockIcon title="Vault" onClick={() => setActiveNav("memory")}>
            ⛁
          </DockIcon>
          <div className="mark-dock-links">
            <button type="button" onClick={() => setShowMessages(!showMessages)}>
              Messages
            </button>
            <span className="text-gray-700">·</span>
            <button type="button" onClick={() => setShowMessages(true)}>
              Chats · {chatCount}
            </button>
            <span className="text-gray-700">·</span>
            <button type="button" onClick={() => setShowMessages(false)}>
              Minimize
            </button>
          </div>
          <div className="flex-1" />
        </div>

        <div className="flex items-center gap-1 border-b border-white/5 pb-2 mb-2 text-[10px] text-muted">
          <span className="text-gray-400">Command</span>
          <div className="flex-1" />
          <button
            type="button"
            onClick={() => {
              const next = !voiceEnabled;
              setVoiceEnabled(next);
              if (!next) stopAudio();
            }}
            className={`px-2 py-0.5 rounded ${voiceEnabled ? "text-accent" : "text-gray-600"}`}
          >
            Voice {voiceEnabled ? "on" : "off"}
          </button>
        </div>

        <div className="flex items-end gap-2">
          <button
            type="button"
            className="mark-dock-plus"
            onClick={() => {
              const input = document.getElementById("mark-command-input") as HTMLInputElement;
              input?.focus();
            }}
          >
            +
          </button>

          <button
            type="button"
            onPointerDown={(e) => {
              e.preventDefault();
              start();
            }}
            onPointerUp={() => stop()}
            onPointerLeave={() => voiceRecording && cancel()}
            className={`shrink-0 w-9 h-9 rounded-full flex items-center justify-center border transition-all ${
              voiceRecording
                ? "border-red-400/50 bg-red-500/20 text-red-300 animate-pulse"
                : "border-accent/30 bg-accent/10 text-accent hover:bg-accent/20"
            }`}
            title="Hold to speak"
          >
            <MicIcon />
          </button>

          <VoiceCommandInput onSend={sendCommand} disabled={voiceRecording || voiceSpeaking} />

          <button
            type="button"
            onClick={() => {
              const input = document.getElementById("mark-command-input") as HTMLInputElement;
              if (input?.value) {
                sendCommand(input.value);
                input.value = "";
              }
            }}
            className="mark-dock-send"
            title="Send"
          >
            <SendIcon />
          </button>
        </div>

        <AnimatePresence>
          {voiceRecording && (
            <motion.p
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="text-[10px] text-accent mt-2 text-center"
            >
              Listening… release to send
            </motion.p>
          )}
          {voiceSpeaking && !voiceRecording && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-[10px] text-emerald-400/80 mt-2 text-center"
            >
              MARK is speaking…
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function VoiceCommandInput({
  onSend,
  disabled,
}: {
  onSend: (t: string) => void;
  disabled?: boolean;
}) {
  return (
    <input
      id="mark-command-input"
      disabled={disabled}
      placeholder="Message MARK…"
      onKeyDown={(e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          const v = (e.target as HTMLInputElement).value;
          if (v.trim()) {
            onSend(v);
            (e.target as HTMLInputElement).value = "";
          }
        }
      }}
      className="flex-1 bg-transparent border-none outline-none text-sm text-white placeholder:text-gray-600 py-2"
    />
  );
}

function DockIcon({
  children,
  title,
  active,
  onClick,
}: {
  children: React.ReactNode;
  title: string;
  active?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      title={title}
      onClick={onClick}
      className={`mark-dock-icon ${active ? "mark-dock-icon--active" : ""}`}
    >
      {children}
    </button>
  );
}

function MicIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 14a3 3 0 003-3V5a3 3 0 10-6 0v6a3 3 0 003 3zm5-3a5 5 0 01-10 0H5a7 7 0 0014 0h-2zm-1 6H8v2h8v-2z" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8-8-8z" />
    </svg>
  );
}
