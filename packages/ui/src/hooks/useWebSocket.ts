import { useEffect, useRef } from "react";
import type { WsEnvelope } from "@mark/shared";
import { api } from "../lib/api";
import { useMarkStore } from "../store/markStore";

const MAX_BACKOFF_MS = 30_000;

export function useWebSocket(token: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const attemptRef = useRef(0);
  const handleWsEvent = useMarkStore((s) => s.handleWsEvent);
  const setWsConnected = useMarkStore((s) => s.setWsConnected);

  useEffect(() => {
    if (!token) return;

    let disposed = false;

    const connect = () => {
      if (disposed) return;
      const ws = new WebSocket(api.wsUrl(token));
      wsRef.current = ws;

      ws.onopen = () => {
        attemptRef.current = 0;
        setWsConnected(true);
      };

      ws.onclose = () => {
        setWsConnected(false);
        if (disposed) return;
        const delay = Math.min(1000 * 2 ** attemptRef.current, MAX_BACKOFF_MS);
        attemptRef.current += 1;
        reconnectRef.current = setTimeout(connect, delay);
      };

      ws.onerror = () => setWsConnected(false);

      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data as string) as WsEnvelope;
          if (data.type === "pong") return;
          handleWsEvent(data);
        } catch {
          /* ignore malformed */
        }
      };
    };

    connect();

    const ping = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "ping", payload: {} }));
      }
    }, 25000);

    return () => {
      disposed = true;
      clearInterval(ping);
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      wsRef.current?.close();
      wsRef.current = null;
      setWsConnected(false);
    };
  }, [token, handleWsEvent, setWsConnected]);

  const send = (event: WsEnvelope) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(event));
    }
  };

  return { send };
}
