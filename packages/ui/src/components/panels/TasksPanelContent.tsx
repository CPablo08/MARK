import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useMarkQueries } from "../../hooks/useMarkQuery";
import { useMarkStore } from "../../store/markStore";
import { api } from "../../lib/api";

export function TasksPanelContent() {
  const token = useMarkStore((s) => s.token);
  const setOpenPanel = useMarkStore((s) => s.setOpenPanel);
  const { tasks } = useMarkQueries();
  const qc = useQueryClient();
  const [title, setTitle] = useState("");
  const [objective, setObjective] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const create = async () => {
    if (!token || !title.trim() || !objective.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const t = await api.createTask(token, {
        title: title.trim(),
        objective: objective.trim(),
      });
      useMarkStore.getState().updateTask({
        task_id: t.id,
        title: t.title,
        status: t.status as import("@mark/shared").TaskStatus,
        progress: t.progress,
        objective: t.objective,
      });
      setTitle("");
      setObjective("");
      await qc.invalidateQueries({ queryKey: ["tasks"] });
      useMarkStore.getState().setOrbState("executing");
      setOpenPanel("ops");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create task");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="p-3 rounded-lg border border-border/80 bg-surface/50 space-y-2">
        <p className="text-[10px] uppercase tracking-wider text-muted">New autonomous task</p>
        <input
          className="mark-bottom-input w-full"
          placeholder="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <textarea
          className="mark-bottom-input w-full min-h-[72px] resize-y"
          placeholder="Objective — what should MARK execute?"
          value={objective}
          onChange={(e) => setObjective(e.target.value)}
        />
        <button
          type="button"
          className="mark-btn mark-btn--primary w-full"
          disabled={busy || !title.trim() || !objective.trim()}
          onClick={create}
        >
          {busy ? "Starting…" : "Run full task pipeline"}
        </button>
        {error && <p className="text-xs text-red-400">{error}</p>}
      </div>

      <div>
        <p className="text-[10px] uppercase tracking-wider text-muted mb-2">Recent tasks</p>
        {tasks.isLoading && <p className="text-sm text-muted">Loading…</p>}
        {tasks.error && <p className="text-sm text-red-400">{tasks.error.message}</p>}
        {!tasks.isLoading && (tasks.data ?? []).length === 0 && (
          <p className="text-sm text-muted">No tasks yet.</p>
        )}
        <ul className="space-y-2">
          {(tasks.data ?? []).map((t) => (
            <li
              key={t.id}
              className="p-3 rounded-lg bg-surface border border-border/60 text-sm"
            >
              <p className="text-gray-200">{t.title}</p>
              <p className="text-[10px] text-accent mt-1 uppercase tracking-wide">
                {t.status} · {Math.round(t.progress)}%
              </p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
