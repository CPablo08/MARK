import { useCallback, useRef } from "react";

function normalizeBase64(raw: string): string {
  return raw.replace(/\s/g, "");
}

function base64ToBytes(b64: string): Uint8Array | null {
  const clean = normalizeBase64(b64);
  if (!clean || clean.length < 32) return null;
  try {
    const bin = atob(clean);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return bytes;
  } catch {
    return null;
  }
}

function mimeForFormat(format: string): string {
  if (format === "wav") return "audio/wav";
  if (format === "ogg") return "audio/ogg";
  return "audio/mpeg";
}

export function useAudioPlayer() {
  const queueRef = useRef<Promise<void>>(Promise.resolve());
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const objectUrlRef = useRef<string | null>(null);

  const revokeObjectUrl = () => {
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
  };

  const playChunk = useCallback((base64: string, format: string, onDone?: () => void) => {
    const bytes = base64ToBytes(base64);
    if (!bytes || bytes.length < 100) {
      console.warn("Audio playback skipped: invalid or empty TTS payload");
      onDone?.();
      return;
    }

    queueRef.current = queueRef.current.then(
      () =>
        new Promise<void>((resolve) => {
          revokeObjectUrl();
          const blob = new Blob([new Uint8Array(bytes)], { type: mimeForFormat(format) });
          const url = URL.createObjectURL(blob);
          objectUrlRef.current = url;

          const audio = new Audio(url);
          audioRef.current = audio;
          audio.volume = 1;

          const finish = () => {
            revokeObjectUrl();
            onDone?.();
            resolve();
          };

          audio.onended = finish;
          audio.onerror = () => {
            console.warn("Audio element error:", audio.error?.message);
            finish();
          };

          void audio.play().catch((err) => {
            console.warn("Audio playback blocked:", err);
            finish();
          });
        })
    );
  }, []);

  const stop = useCallback(() => {
    audioRef.current?.pause();
    if (audioRef.current) audioRef.current.currentTime = 0;
    revokeObjectUrl();
    queueRef.current = Promise.resolve();
  }, []);

  return { playChunk, stop };
}
