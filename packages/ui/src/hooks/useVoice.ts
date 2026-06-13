import { useCallback, useRef, useState } from "react";
import { api } from "../lib/api";
import { useMarkStore } from "../store/markStore";

type SpeechRecognitionCtor = new () => SpeechRecognition;

function getSpeechRecognition(): SpeechRecognitionCtor | null {
  if (typeof window === "undefined") return null;
  const w = window as Window & {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

function pickMimeType(): string {
  const types = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/mp4",
    "audio/ogg;codecs=opus",
  ];
  for (const t of types) {
    if (MediaRecorder.isTypeSupported(t)) return t;
  }
  return "";
}

const UTTERANCE_PAUSE_MS = 1100;

export function useVoice(onUtterance: (text: string) => void | Promise<void>) {
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const mimeRef = useRef("webm");
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const rafRef = useRef<number>(0);
  const streamRef = useRef<MediaStream | null>(null);
  const speechRef = useRef<SpeechRecognition | null>(null);
  const transcriptRef = useRef("");
  const finalBufferRef = useRef("");
  const utteranceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pausedRef = useRef(false);
  const sendingRef = useRef(false);
  const conversationRef = useRef(false);

  const [isConversationActive, setIsConversationActive] = useState(false);

  const setAmplitude = useMarkStore((s) => s.setVoiceAmplitude);
  const setRecording = useMarkStore((s) => s.setVoiceRecording);
  const setVoiceTranscript = useMarkStore((s) => s.setVoiceTranscript);
  const setVoiceError = useMarkStore((s) => s.setVoiceError);
  const setOrbState = useMarkStore((s) => s.setOrbState);
  const token = useMarkStore((s) => s.token);

  const tickAmplitude = useCallback(() => {
    const analyser = analyserRef.current;
    if (!analyser) return;
    const data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(data);
    const avg = data.reduce((a, b) => a + b, 0) / data.length / 255;
    setAmplitude(avg);
    rafRef.current = requestAnimationFrame(tickAmplitude);
  }, [setAmplitude]);

  const clearUtteranceTimer = useCallback(() => {
    if (utteranceTimerRef.current) {
      clearTimeout(utteranceTimerRef.current);
      utteranceTimerRef.current = null;
    }
  }, []);

  const applyTranscript = useCallback(
    (text: string) => {
      transcriptRef.current = text;
      setVoiceTranscript(text);
    },
    [setVoiceTranscript]
  );

  const transcribeBlob = useCallback(
    async (blob: Blob): Promise<string> => {
      if (!token || blob.size < 200) return "";
      const format = mimeRef.current.includes("webm")
        ? "webm"
        : mimeRef.current.includes("ogg")
          ? "ogg"
          : mimeRef.current.includes("mp4")
            ? "mp4"
            : "webm";

      const base64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          const dataUrl = reader.result as string;
          resolve(dataUrl.split(",")[1] ?? "");
        };
        reader.onerror = () => reject(new Error("Failed to read audio"));
        reader.readAsDataURL(blob);
      });

      const res = await api.voice.transcribe(token, base64, format);
      return res.text?.trim() ?? "";
    },
    [token]
  );

  const stopMicCapture = useCallback(() => {
    speechRef.current?.stop();
    speechRef.current = null;
    setRecording(false);
    cancelAnimationFrame(rafRef.current);
    setAmplitude(0);
  }, [setAmplitude, setRecording]);

  const flushUtterance = useCallback(async () => {
    if (sendingRef.current || pausedRef.current) return;
    const text = (finalBufferRef.current || transcriptRef.current).trim();
    if (!text) return;

    sendingRef.current = true;
    clearUtteranceTimer();
    stopMicCapture();
    finalBufferRef.current = "";
    transcriptRef.current = "";
    setVoiceTranscript("");
    setOrbState("thinking");

    try {
      await onUtterance(text);
    } finally {
      sendingRef.current = false;
      if (conversationRef.current && !pausedRef.current) {
        setOrbState("listening");
      }
    }
  }, [clearUtteranceTimer, onUtterance, setOrbState, setVoiceTranscript, stopMicCapture]);

  const scheduleUtteranceEnd = useCallback(() => {
    clearUtteranceTimer();
    utteranceTimerRef.current = setTimeout(() => {
      void flushUtterance();
    }, UTTERANCE_PAUSE_MS);
  }, [clearUtteranceTimer, flushUtterance]);

  const teardownMedia = useCallback(() => {
    cancelAnimationFrame(rafRef.current);
    setAmplitude(0);
    setRecording(false);

    speechRef.current?.stop();
    speechRef.current = null;

    if (mediaRef.current?.state === "recording") {
      mediaRef.current.onstop = null;
      mediaRef.current.stop();
    }
    mediaRef.current = null;
    chunksRef.current = [];

    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    audioCtxRef.current?.close().catch(() => {});
    audioCtxRef.current = null;
  }, [setAmplitude, setRecording]);

  const startListening = useCallback(async () => {
    if (!token || pausedRef.current) return;
    setVoiceError(null);

    const SpeechRecognition = getSpeechRecognition();
    if (!SpeechRecognition) {
      setVoiceError("Voice conversation requires Chrome or Edge (speech recognition).");
      return;
    }

    try {
      if (!streamRef.current) {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        });
        streamRef.current = stream;

        const ctx = new AudioContext();
        audioCtxRef.current = ctx;
        const source = ctx.createMediaStreamSource(stream);
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        analyserRef.current = analyser;

        const mime = pickMimeType();
        mimeRef.current = mime || "audio/webm";
        const recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) chunksRef.current.push(e.data);
        };
        mediaRef.current = recorder;
        recorder.start(250);
      }

      if (speechRef.current) return;

      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = navigator.language || "en-US";
      recognition.onresult = (event) => {
        if (pausedRef.current || sendingRef.current) return;
        let interim = "";
        let finals = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const part = event.results[i][0]?.transcript ?? "";
          if (event.results[i].isFinal) finals += part;
          else interim += part;
        }
        if (finals) {
          finalBufferRef.current = `${finalBufferRef.current} ${finals}`.trim();
        }
        const display = (finalBufferRef.current + " " + interim).trim();
        if (display) applyTranscript(display);
        if (finals.trim()) scheduleUtteranceEnd();
      };
      recognition.onerror = (event) => {
        if (event.error === "not-allowed") {
          setVoiceError("Microphone access denied.");
          conversationRef.current = false;
          setIsConversationActive(false);
          teardownMedia();
        }
      };
      recognition.addEventListener("end", () => {
        if (conversationRef.current && !pausedRef.current && !sendingRef.current) {
          try {
            recognition.start();
          } catch {
            /* restart */
          }
        }
      });
      recognition.start();
      speechRef.current = recognition;

      setRecording(true);
      setOrbState("listening");
      rafRef.current = requestAnimationFrame(tickAmplitude);
    } catch {
      setVoiceError("Microphone access denied or unavailable.");
      conversationRef.current = false;
      setIsConversationActive(false);
      teardownMedia();
      setOrbState("idle");
    }
  }, [
    token,
    applyTranscript,
    scheduleUtteranceEnd,
    setAmplitude,
    setRecording,
    setOrbState,
    setVoiceError,
    teardownMedia,
    tickAmplitude,
  ]);

  const startConversation = useCallback(async () => {
    conversationRef.current = true;
    pausedRef.current = false;
    sendingRef.current = false;
    finalBufferRef.current = "";
    transcriptRef.current = "";
    setIsConversationActive(true);
    await startListening();
  }, [startListening]);

  const endConversation = useCallback(() => {
    conversationRef.current = false;
    pausedRef.current = false;
    sendingRef.current = false;
    clearUtteranceTimer();
    finalBufferRef.current = "";
    transcriptRef.current = "";
    setVoiceTranscript("");
    setVoiceError(null);
    setIsConversationActive(false);
    teardownMedia();
    setOrbState("idle");
  }, [clearUtteranceTimer, setOrbState, setVoiceError, setVoiceTranscript, teardownMedia]);

  const pauseForReply = useCallback(() => {
    pausedRef.current = true;
    clearUtteranceTimer();
    stopMicCapture();
  }, [clearUtteranceTimer, stopMicCapture]);

  const resumeAfterReply = useCallback(() => {
    if (!conversationRef.current) return;
    pausedRef.current = false;
    finalBufferRef.current = "";
    transcriptRef.current = "";
    setVoiceTranscript("");
    void startListening();
  }, [setVoiceTranscript, startListening]);

  /** @deprecated legacy hold-to-talk — use startConversation */
  const start = startConversation;
  const stop = () => void flushUtterance();
  const cancel = endConversation;

  return {
    startConversation,
    endConversation,
    pauseForReply,
    resumeAfterReply,
    isConversationActive,
    start,
    stop,
    cancel,
  };
}
