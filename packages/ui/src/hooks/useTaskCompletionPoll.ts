import { useEffect, useRef } from "react";
import type { TaskUpdatedPayload } from "@mark/shared";
import { api } from "../lib/api";
import { useMarkStore } from "../store/markStore";

const ACTIVE = new Set(["pending", "queued", "running", "awaiting_approval"]);
const TERMINAL = new Set(["completed", "failed"]);

/** Lightweight poll so completion toasts work even when Ops is closed. */
export function useTaskCompletionPoll(token: string | null) {
  const tasks = useMarkStore((s) => s.tasks);
  const hasActive = tasks.some((t) => ACTIVE.has(t.status));
  const prevStatusRef = useRef<Map<string, string>>(new Map());

  useEffect(() => {
    if (!token || !hasActive) return;

    let cancelled = false;

    const tick = async () => {
      try {
        const rows = await api.tasks(token);
        if (cancelled) return;
        for (const t of rows) {
          const prev = prevStatusRef.current.get(t.id);
          if (
            prev &&
            ACTIVE.has(prev) &&
            TERMINAL.has(t.status) &&
            !useMarkStore.getState().notifiedTaskIds.has(t.id)
          ) {
            const result = await api.taskResult(token, t.id);
            if (result.result_content || result.result_preview) {
              useMarkStore.getState().notifyTaskComplete({
                task_id: result.task_id,
                title: result.title,
                status: t.status as TaskUpdatedPayload["status"],
                progress: 100,
                result_message_id: result.result_message_id ?? undefined,
                result_kind: result.result_kind as TaskUpdatedPayload["result_kind"],
                result_preview: result.result_preview ?? undefined,
                result_content: result.result_content ?? undefined,
              });
            }
          }
          prevStatusRef.current.set(t.id, t.status);
        }
      } catch {
        /* ignore */
      }
    };

    tick();
    const id = setInterval(tick, 3000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [token, hasActive]);
}
