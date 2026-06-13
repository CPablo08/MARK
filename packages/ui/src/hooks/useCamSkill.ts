import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { useMarkStore } from "../store/markStore";

export interface CamDetection {
  class: string;
  score: number;
  x: number;
  y: number;
  width: number;
  height: number;
}

type CocoModel = {
  detect: (input: HTMLVideoElement | HTMLCanvasElement) => Promise<
    Array<{ class: string; score: number; bbox: [number, number, number, number] }>
  >;
};

export function useCamSkill(active: boolean) {
  const token = useMarkStore((s) => s.token);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const modelRef = useRef<CocoModel | null>(null);
  const rafRef = useRef<number>(0);

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [detections, setDetections] = useState<CamDetection[]>([]);
  const [modelReady, setModelReady] = useState(false);

  const loadModel = useCallback(async () => {
    if (modelRef.current) return;
    setLoading(true);
    try {
      const tf = await import("@tensorflow/tfjs");
      await tf.ready();
      const coco = await import("@tensorflow-models/coco-ssd");
      modelRef.current = await coco.load({ base: "lite_mobilenet_v2" });
      setModelReady(true);
    } catch (e) {
      setError(
        e instanceof Error
          ? `CV model failed to load: ${e.message}`
          : "CV model failed to load"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
  }, []);

  const uploadFrame = useCallback(
    async (canvas: HTMLCanvasElement, dets: CamDetection[]) => {
      if (!token) return;
      const dataUrl = canvas.toDataURL("image/jpeg", 0.72);
      const image_base64 = dataUrl.split(",")[1] ?? "";
      try {
        await api.camFrame(token, {
          image_base64,
          width: canvas.width,
          height: canvas.height,
          detections: dets.map((d) => ({
            class: d.class,
            score: d.score,
            x: d.x,
            y: d.y,
            width: d.width,
            height: d.height,
          })),
        });
      } catch {
        /* API may be down */
      }
    },
    [token]
  );

  useEffect(() => {
    if (!active) {
      stopCamera();
      setDetections([]);
      return;
    }

    let cancelled = false;
    void loadModel();

    (async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        const video = videoRef.current;
        if (video) {
          video.srcObject = stream;
          await video.play();
        }
      } catch (e) {
        setError(
          e instanceof Error
            ? e.message
            : "Camera permission denied or unavailable"
        );
      }
    })();

    return () => {
      cancelled = true;
      stopCamera();
    };
  }, [active, loadModel, stopCamera]);

  useEffect(() => {
    if (!active || !modelReady) return;

    let lastUpload = 0;
    let uploadedOnce = false;
    const tick = async () => {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const model = modelRef.current;
      if (!video || !canvas || !model || video.readyState < 2) {
        rafRef.current = requestAnimationFrame(tick);
        return;
      }

      const w = video.videoWidth;
      const h = video.videoHeight;
      if (w > 0 && h > 0) {
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext("2d");
        if (ctx) {
          ctx.drawImage(video, 0, 0, w, h);
          try {
            const raw = await model.detect(video);
            const mapped: CamDetection[] = raw.map((r) => ({
              class: r.class,
              score: r.score,
              x: r.bbox[0],
              y: r.bbox[1],
              width: r.bbox[2],
              height: r.bbox[3],
            }));
            setDetections(mapped);
            ctx.strokeStyle = "rgba(74, 109, 148, 0.9)";
            ctx.lineWidth = 2;
            ctx.font = "12px system-ui";
            for (const d of mapped) {
              ctx.strokeRect(d.x, d.y, d.width, d.height);
              const label = `${d.class} ${Math.round(d.score * 100)}%`;
              ctx.fillStyle = "rgba(10, 12, 16, 0.75)";
              ctx.fillRect(d.x, d.y - 18, ctx.measureText(label).width + 8, 18);
              ctx.fillStyle = "#c5d4e8";
              ctx.fillText(label, d.x + 4, d.y - 5);
            }
            const now = Date.now();
            if (!uploadedOnce || now - lastUpload > 2000) {
              lastUpload = now;
              uploadedOnce = true;
              void uploadFrame(canvas, mapped);
            }
          } catch {
            /* skip frame */
          }
        }
      }
      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [active, modelReady, uploadFrame]);

  return {
    videoRef,
    canvasRef,
    error,
    loading,
    detections,
    modelReady,
    stopCamera,
  };
}
