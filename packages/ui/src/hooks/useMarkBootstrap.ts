import { useEffect } from "react";
import { api } from "../lib/api";
import { useMarkStore } from "../store/markStore";

/** Load recent tasks for Ops (active + recently finished). */
export function useMarkBootstrap(token: string | null) {
  const setTasks = useMarkStore((s) => s.setTasks);

  useEffect(() => {
    if (!token) return;

    api.tasks(token).then((tasks) => {
      setTasks(
        tasks.slice(0, 25).map((t) => ({
          task_id: t.id,
          title: t.title,
          status: t.status,
          progress: t.progress,
          objective: t.objective,
        }))
      );
    });
  }, [token, setTasks]);
}
