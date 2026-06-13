import { useEffect, useRef } from "react";
import type { AgentInstance, AgentStatusPayload, TaskUpdatedPayload } from "@mark/shared";
import { api } from "../lib/api";
import { useMarkStore } from "../store/markStore";

const ACTIVE = new Set(["pending", "queued", "running", "awaiting_approval"]);
const TERMINAL = new Set(["completed", "failed"]);

function mapAgent(a: AgentInstance): AgentStatusPayload {
  return {
    agent_id: a.id,
    role: a.role as AgentStatusPayload["role"],
    status: a.status as AgentStatusPayload["status"],
    task_id: a.task_id ?? undefined,
  };
}

/** Poll tasks/agents/feed when Ops is open or tasks are running (WS fallback). */
export function useOpsSync(token: string | null) {
  const openPanel = useMarkStore((s) => s.openPanel);
  const tasks = useMarkStore((s) => s.tasks);
  const setTasks = useMarkStore((s) => s.setTasks);
  const setAgents = useMarkStore((s) => s.setAgents);
  const pushFeed = useMarkStore((s) => s.pushFeed);
  const prevStatusRef = useRef<Map<string, string>>(new Map());

  const hasActive = tasks.some((t) => ACTIVE.has(t.status));
  const shouldPoll = !!token && (openPanel === "ops" || hasActive);

  useEffect(() => {
    if (!token) return;

    let cancelled = false;

    const sync = async () => {
      try {
        const [taskRows, agentRows] = await Promise.all([
          api.tasks(token),
          api.agents(token),
        ]);
        if (cancelled) return;

        for (const t of taskRows) {
          const prev = prevStatusRef.current.get(t.id);
          if (
            prev &&
            ACTIVE.has(prev) &&
            TERMINAL.has(t.status) &&
            !useMarkStore.getState().notifiedTaskIds.has(t.id)
          ) {
            try {
              const result = await api.taskResult(token, t.id);
              if (!cancelled && (result.result_content || result.result_preview)) {
                useMarkStore.getState().notifyTaskComplete({
                  task_id: result.task_id,
                  title: result.title,
                  status: result.status as TaskUpdatedPayload["status"],
                  progress: 100,
                  result_message_id: result.result_message_id ?? undefined,
                  result_kind: result.result_kind as TaskUpdatedPayload["result_kind"],
                  result_preview: result.result_preview ?? undefined,
                  result_content: result.result_content ?? undefined,
                });
              }
            } catch {
              /* result not ready yet */
            }
          }
          prevStatusRef.current.set(t.id, t.status);
        }

        const mapped: TaskUpdatedPayload[] = taskRows.slice(0, 30).map((t) => ({
          task_id: t.id,
          title: t.title,
          status: t.status as TaskUpdatedPayload["status"],
          progress: t.progress,
          objective: t.objective,
        }));
        setTasks(mapped);
        setAgents(agentRows.map(mapAgent));

        const running = taskRows.filter((t) => ACTIVE.has(t.status));
        for (const t of running.slice(0, 3)) {
          const feed = await api.taskFeed(token, t.id);
          if (cancelled) return;
          const existing = useMarkStore.getState().executionFeed;
          const known = new Set(existing.map((e) => `${e.task_id}:${e.line}`));
          for (const row of feed) {
            const key = `${t.id}:${row.line}`;
            if (!known.has(key)) {
              pushFeed({ task_id: t.id, line: row.line, level: row.level as "info" });
            }
          }
        }
      } catch {
        /* API may be restarting */
      }
    };

    if (!shouldPoll) return;

    sync();
    const id = setInterval(sync, 2500);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [shouldPoll, token, setTasks, setAgents, pushFeed]);
}
