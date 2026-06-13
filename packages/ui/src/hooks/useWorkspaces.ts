import { useCallback, useEffect, useState } from "react";
import type { ChatMessage } from "../store/markStore";

export interface Workspace {
  id: string;
  name: string;
  sessionId: string | null;
  messages: ChatMessage[];
  updatedAt: number;
}

const STORAGE_KEY = "mark_workspaces";
const ACTIVE_KEY = "mark_active_workspace";

function loadWorkspaces(): Workspace[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as Workspace[];
  } catch {
    return [];
  }
}

function saveWorkspaces(list: Workspace[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
}

export function useWorkspaces(
  messages: ChatMessage[],
  sessionId: string | null,
  onLoad: (ws: Workspace) => void
) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>(() => loadWorkspaces());
  const [activeId, setActiveId] = useState<string | null>(
    () => localStorage.getItem(ACTIVE_KEY) || null
  );
  const [toast, setToast] = useState<string | null>(null);

  const active = workspaces.find((w) => w.id === activeId) ?? workspaces[0] ?? null;

  useEffect(() => {
    if (workspaces.length === 0) {
      const initial: Workspace = {
        id: crypto.randomUUID(),
        name: "Default workspace",
        sessionId: null,
        messages: [],
        updatedAt: Date.now(),
      };
      setWorkspaces([initial]);
      setActiveId(initial.id);
      localStorage.setItem(ACTIVE_KEY, initial.id);
      saveWorkspaces([initial]);
    }
  }, [workspaces.length]);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3500);
  };

  const persistActive = useCallback(
    (patch: Partial<Workspace>) => {
      if (!activeId) return;
      setWorkspaces((list) => {
        const next = list.map((w) =>
          w.id === activeId
            ? { ...w, ...patch, updatedAt: Date.now() }
            : w
        );
        saveWorkspaces(next);
        return next;
      });
    },
    [activeId]
  );

  const select = (id: string) => {
    const ws = workspaces.find((w) => w.id === id);
    if (!ws) return;
    setActiveId(id);
    localStorage.setItem(ACTIVE_KEY, id);
    onLoad(ws);
  };

  const createNew = () => {
    const ws: Workspace = {
      id: crypto.randomUUID(),
      name: `Workspace ${workspaces.length + 1}`,
      sessionId: null,
      messages: [],
      updatedAt: Date.now(),
    };
    const next = [...workspaces, ws];
    setWorkspaces(next);
    saveWorkspaces(next);
    setActiveId(ws.id);
    localStorage.setItem(ACTIVE_KEY, ws.id);
    onLoad(ws);
    showToast("Workspace created.");
  };

  const save = useCallback(() => {
    persistActive({ messages, sessionId });
    showToast("Workspace saved.");
  }, [messages, sessionId, persistActive]);

  const remove = () => {
    if (workspaces.length <= 1) {
      showToast("Cannot delete the only workspace.");
      return;
    }
    const next = workspaces.filter((w) => w.id !== activeId);
    setWorkspaces(next);
    saveWorkspaces(next);
    const fallback = next[0];
    setActiveId(fallback.id);
    localStorage.setItem(ACTIVE_KEY, fallback.id);
    onLoad(fallback);
    showToast("Workspace deleted.");
  };

  const rename = (name: string) => {
    if (!activeId) return;
    persistActive({ name });
  };

  const clearToast = () => setToast(null);

  return {
    workspaces,
    active,
    activeId,
    toast,
    select,
    createNew,
    save,
    remove,
    rename,
    showToast,
    clearToast,
  };
}
