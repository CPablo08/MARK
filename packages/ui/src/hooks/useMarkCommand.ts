import { useCallback, useEffect, useRef } from "react";
import { api } from "../lib/api";
import { getChatLoadingLabel, shouldKeepWorkspaceFocus } from "../lib/skillIntent";
import { useMarkStore } from "../store/markStore";
import { useVoice } from "./useVoice";
import { useAudioPlayer } from "./useAudioPlayer";

/** Unlock browser audio after a user gesture (mic click). */
async function unlockAudioPlayback(): Promise<void> {
  try {
    const Ctx = window.AudioContext || (window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (Ctx) {
      const ctx = new Ctx();
      await ctx.resume();
      const buffer = ctx.createBuffer(1, 1, 22050);
      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(ctx.destination);
      source.start(0);
      await ctx.close();
    }
    // Minimal valid MP3 frame (silence) — avoids corrupt data-URI unlock failures
    const silentBytes = Uint8Array.from([
      0xff, 0xfb, 0x90, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ]);
    const blob = new Blob([silentBytes], { type: "audio/mpeg" });
    const url = URL.createObjectURL(blob);
    const silent = new Audio(url);
    silent.volume = 0.01;
    try {
      await silent.play();
    } finally {
      URL.revokeObjectURL(url);
    }
  } catch {
    /* gesture may still carry through */
  }
}

export function useMarkCommand() {
  const token = useMarkStore((s) => s.token);
  const sessionId = useMarkStore((s) => s.sessionId);
  const setSessionId = useMarkStore((s) => s.setSessionId);
  const setChatMode = useMarkStore((s) => s.setChatMode);
  const addMessage = useMarkStore((s) => s.addMessage);
  const upsertMessage = useMarkStore((s) => s.upsertMessage);
  const setOrbState = useMarkStore((s) => s.setOrbState);
  const setShowMessages = useMarkStore((s) => s.setShowMessages);
  const setOpenPanel = useMarkStore((s) => s.setOpenPanel);
  const voiceSessionActive = useMarkStore((s) => s.voiceSessionActive);
  const setVoiceSessionActive = useMarkStore((s) => s.setVoiceSessionActive);
  const setVoiceError = useMarkStore((s) => s.setVoiceError);

  const speakingRef = useRef(false);
  const lastSpokenIdRef = useRef<string | null>(null);
  const voiceResumeRef = useRef<(() => void) | null>(null);
  const audioUnlockedRef = useRef(false);

  const { playChunk, stop: stopAudio } = useAudioPlayer();

  const speakAssistant = useCallback(
    async (content: string, messageId?: string) => {
      if (!token || !content.trim()) return;
      if (messageId && lastSpokenIdRef.current === messageId) return;
      if (messageId) lastSpokenIdRef.current = messageId;

      const plain = content
        .replace(/[#*_`>\[\]]/g, "")
        .replace(/\n+/g, " ")
        .trim()
        .slice(0, useMarkStore.getState().voiceSessionActive ? 520 : 600);
      if (!plain) return;

      if (!audioUnlockedRef.current) {
        await unlockAudioPlayback();
        audioUnlockedRef.current = true;
      }

      pauseForReplyRef.current?.();
      speakingRef.current = true;
      useMarkStore.getState().setVoiceSpeaking(true);

      try {
        const res = await api.voice.speak(token, plain);
        if (res.ok && res.audio && res.audio.length > 64) {
          await new Promise<void>((resolve) => {
            playChunk(res.audio!, res.format || "mp3", () => resolve());
          });
        } else if (res.error) {
          setVoiceError(res.error);
        } else if (!res.ok) {
          setVoiceError("Voice output unavailable — check ELEVENLABS_API_KEY in .env");
        }
      } catch (e) {
        setVoiceError(e instanceof Error ? e.message : "Voice playback failed");
      } finally {
        speakingRef.current = false;
        useMarkStore.getState().setVoiceSpeaking(false);
        const mode = useMarkStore.getState().chatMode;
        const inVoice = useMarkStore.getState().voiceSessionActive;
        useMarkStore.getState().setOrbState(
          inVoice ? "listening" : mode === "task" ? "executing" : "idle"
        );
        if (inVoice) voiceResumeRef.current?.();
      }
    },
    [token, playChunk, setVoiceError]
  );

  const pauseForReplyRef = useRef<(() => void) | null>(null);

  const sendCommand = useCallback(
    async (content: string, options?: { forVoice?: boolean; newChat?: boolean }) => {
      if (!content.trim() || !token) return;

      const forVoice = options?.forVoice ?? false;
      const newChat = options?.newChat ?? false;

      const userMessageId = crypto.randomUUID();
      addMessage({ id: userMessageId, role: "user", content: content.trim() });
      setOrbState("thinking");
      const loadingLabel = getChatLoadingLabel(content);
      useMarkStore.getState().setChatLoadingLabel(loadingLabel);
      const workspaceMode = useMarkStore.getState().workspaceMode;
      if (!shouldKeepWorkspaceFocus(content, workspaceMode)) {
        setShowMessages(true);
        setOpenPanel("messages");
      } else {
        setOpenPanel(null);
      }

      const placeholderId = crypto.randomUUID();
      upsertMessage({
        id: placeholderId,
        role: "assistant",
        content: `…${loadingLabel}…`,
        streaming: true,
      });

      try {
        const activeSession = useMarkStore.getState().sessionId;
        const forceNew = newChat || !activeSession;
        const { contextTaskId, taskNotification } = useMarkStore.getState();
        const reportTaskId =
          contextTaskId ?? taskNotification?.taskId ?? undefined;
        const res = await api.chat(token, {
          content: content.trim(),
          session_id: forceNew ? undefined : activeSession ?? undefined,
          new_chat: forceNew,
          for_voice: forVoice,
          client_message_id: userMessageId,
          task_id: reportTaskId,
        });
        if (res.session_id) {
          setSessionId(res.session_id);
          localStorage.setItem("mark_session_id", res.session_id);
        }
        setChatMode(res.intent === "task" ? "task" : "chat");

        const hasArtifact = Boolean(res.briefing || res.visualize);
        if (hasArtifact) {
          useMarkStore.setState({ openPanel: null, showMessages: false });
        }

        if (res.briefing) {
          useMarkStore.getState().openBriefing({
            id: res.briefing.id,
            query: res.briefing.query,
            title: res.briefing.title,
            summary: res.briefing.summary,
            kind: res.briefing.kind as import("@mark/shared").BriefingKind | undefined,
            image_url: res.briefing.image_url,
            image_source: res.briefing.image_source,
            images: res.briefing.images,
            facts: res.briefing.facts,
            sources: res.briefing.sources,
            market: res.briefing.market,
          });
        } else if (res.visualize) {
          useMarkStore.getState().openVisualize({
            id: res.visualize.id,
            title: res.visualize.title,
            html: res.visualize.html,
            description: res.visualize.description,
          });
        }

        if (res.assistant_message_id && res.assistant_content) {
          upsertMessage({
            id: res.assistant_message_id,
            role: "assistant",
            content: res.assistant_content,
            streaming: false,
          });
          useMarkStore.setState((s) => ({
            messages: s.messages.filter((m) => m.id !== placeholderId),
          }));
          const shouldSpeak =
            forVoice ||
            useMarkStore.getState().voiceSessionActive ||
            useMarkStore.getState().voiceSpeaking;
          if (shouldSpeak) {
            if (hasArtifact) {
              await new Promise((r) => setTimeout(r, 150));
            }
            await speakAssistant(res.assistant_content, res.assistant_message_id);
          }
        } else {
          useMarkStore.setState((s) => ({
            messages: s.messages.filter((m) => m.id !== placeholderId),
          }));
        }

        if (res.intent === "task") {
          if (res.task) {
            useMarkStore.getState().updateTask({
              task_id: res.task.task_id,
              title: res.task.title,
              status: res.task.status as import("@mark/shared").TaskStatus,
              progress: res.task.progress,
              objective: res.task.objective,
            });
          } else if (res.task_id) {
            useMarkStore.getState().updateTask({
              task_id: res.task_id,
              title: content.trim().slice(0, 120),
              status: "running",
              progress: 0,
              objective: content.trim(),
            });
          }
          setOrbState("executing");
          setOpenPanel("ops");
        } else if (!speakingRef.current) {
          setOrbState("idle");
        }
      } catch (e) {
        useMarkStore.setState((s) => ({
          messages: s.messages.filter((m) => m.id !== placeholderId),
        }));
        addMessage({
          id: crypto.randomUUID(),
          role: "assistant",
          content: `**Error:** ${e instanceof Error ? e.message : "Failed"}`,
        });
        setOrbState("idle");
      } finally {
        useMarkStore.getState().setChatLoadingLabel(null);
      }
    },
    [
      token,
      sessionId,
      addMessage,
      upsertMessage,
      setOrbState,
      setSessionId,
      setShowMessages,
      setOpenPanel,
      setChatMode,
      speakAssistant,
    ]
  );

  const onVoiceUtterance = useCallback(
    (text: string) => sendCommand(text, { forVoice: true }),
    [sendCommand]
  );

  const {
    startConversation,
    endConversation,
    pauseForReply,
    resumeAfterReply,
    isConversationActive,
  } = useVoice(onVoiceUtterance);

  voiceResumeRef.current = resumeAfterReply;
  pauseForReplyRef.current = pauseForReply;

  const toggleVoiceSession = useCallback(() => {
    if (isConversationActive || voiceSessionActive) {
      endConversation();
      setVoiceSessionActive(false);
      setOrbState("idle");
    } else {
      useMarkStore.getState().startNewChat();
      setVoiceSessionActive(true);
      setVoiceError(null);
      audioUnlockedRef.current = false;
      void unlockAudioPlayback().then(() => {
        audioUnlockedRef.current = true;
        void startConversation();
      });
    }
  }, [
    isConversationActive,
    voiceSessionActive,
    endConversation,
    startConversation,
    setVoiceSessionActive,
    setOrbState,
    setVoiceError,
  ]);

  useEffect(() => {
    const onAssistant = (e: Event) => {
      const detail = (e as CustomEvent).detail as {
        content?: string;
        speak?: boolean;
        message_id?: string;
      };
      if (detail.speak === false) return;
      if (!detail.content?.trim()) return;
      const inVoice =
        useMarkStore.getState().voiceSessionActive || useMarkStore.getState().voiceSpeaking;
      if (!inVoice) return;
      void speakAssistant(detail.content, detail.message_id);
    };

    window.addEventListener("mark:assistant-message", onAssistant);
    return () => window.removeEventListener("mark:assistant-message", onAssistant);
  }, [speakAssistant]);

  return {
    sendCommand,
    toggleVoiceSession,
    voiceSessionActive: voiceSessionActive || isConversationActive,
    stopAudio,
  };
}
