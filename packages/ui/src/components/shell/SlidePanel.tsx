import { useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useQueryClient } from "@tanstack/react-query";
import { useMarkStore, type ChatMessage, type PanelId } from "../../store/markStore";
import { ConversationStream } from "../chat/ConversationStream";
import { OperationsPanel } from "./OperationsPanel";
import { WorkspacePanel } from "../home/WorkspacePanel";
import { TasksPanelContent } from "../panels/TasksPanelContent";
import { PluginsPanel } from "../panels/PluginsPanel";
import { ChatHistoryPanel } from "../panels/ChatHistoryPanel";
import { AgentsPage, SettingsPage } from "../../pages/GenericPage";
import { VaultPage } from "../../pages/VaultPage";

const TITLES: Record<PanelId, string> = {
  messages: "Messages",
  ops: "Operations",
  workspace: "Workspaces",
  tasks: "Tasks",
  agents: "Agents",
  vault: "Memory vault",
  logs: "Chat history",
  integrations: "Plugins",
  settings: "Settings",
};

const TALL: PanelId[] = ["vault", "messages"];

const REFRESH_KEYS: Partial<Record<PanelId, string[]>> = {
  tasks: ["tasks"],
  agents: ["agents"],
  vault: ["memory-graph", "memory"],
  logs: ["sessions"],
  integrations: ["plugins-catalog", "integrations"],
  ops: ["tasks", "agents"],
};

export function SlidePanel() {
  const openPanel = useMarkStore((s) => s.openPanel);
  const workspaceMode = useMarkStore((s) => s.workspaceMode);
  const setOpenPanel = useMarkStore((s) => s.setOpenPanel);
  const messages = useMarkStore((s) => s.messages);
  const token = useMarkStore((s) => s.token);
  const qc = useQueryClient();

  const panelId =
    workspaceMode !== "idle" && openPanel === "messages" ? null : openPanel;

  useEffect(() => {
    if (!panelId || !token) return;
    const keys = REFRESH_KEYS[panelId];
    if (keys) keys.forEach((k) => qc.invalidateQueries({ queryKey: [k] }));
  }, [panelId, token, qc]);

  useEffect(() => {
    if (workspaceMode !== "idle" && openPanel === "messages") {
      setOpenPanel(null);
    }
  }, [workspaceMode, openPanel, setOpenPanel]);

  return (
    <AnimatePresence>
      {panelId && (
        <>
          <motion.button
            type="button"
            className="mark-panel-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setOpenPanel(null)}
            aria-label="Close panel"
          />
          <motion.div
            className={`mark-panel-sheet ${TALL.includes(panelId) ? "mark-panel-sheet--tall" : ""}`}
            initial={{ y: "100%", opacity: 0.9 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: "100%", opacity: 0.9 }}
            transition={{ type: "spring", damping: 28, stiffness: 320 }}
          >
            <div className="mark-panel-header">
              <h2 className="mark-panel-title">{TITLES[panelId]}</h2>
              <motion.div className="flex items-center gap-2">
                {panelId === "messages" && (
                  <button
                    type="button"
                    className="text-[10px] uppercase tracking-wider text-muted hover:text-accent px-2 py-1 rounded border border-border/60"
                    onClick={() => useMarkStore.getState().startNewChat()}
                  >
                    New chat
                  </button>
                )}
                <button
                  type="button"
                  className="mark-panel-close"
                  onClick={() => setOpenPanel(null)}
                  aria-label="Close"
                >
                  ✕
                </button>
              </motion.div>
            </div>
            <div className="mark-panel-body">
              <PanelBody id={panelId} messages={messages} />
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function PanelBody({ id, messages }: { id: PanelId; messages: ChatMessage[] }) {
  switch (id) {
    case "messages":
      return (
        <div className="h-full min-h-[280px] flex flex-col">
          <ConversationStream messages={messages} />
        </div>
      );
    case "ops":
      return <OperationsPanel />;
    case "workspace":
      return <WorkspacePanel />;
    case "tasks":
      return <TasksPanelContent />;
    case "agents":
      return <PanelPageWrap><AgentsPage /></PanelPageWrap>;
    case "vault":
      return (
        <div className="h-[min(70vh,560px)] min-h-0 -mx-1">
          <VaultPage />
        </div>
      );
    case "logs":
      return <PanelPageWrap><ChatHistoryPanel /></PanelPageWrap>;
    case "integrations":
      return <PluginsPanel />;
    case "settings":
      return <PanelPageWrap><SettingsPage /></PanelPageWrap>;
    default:
      return null;
  }
}

function PanelPageWrap({ children }: { children: React.ReactNode }) {
  return <div className="mark-panel-page">{children}</div>;
}
