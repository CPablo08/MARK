import { create } from "zustand";
import type {
  AgentStatusPayload,
  ApprovalRequestPayload,
  CamSkillOpenPayload,
  ExecutionFeedPayload,
  MetricsSnapshotPayload,
  OrbState,
  TaskResultKind,
  TaskUpdatedPayload,
  BriefingOpenPayload,
  VisualizeOpenPayload,
  WorkspaceMode,
  WsEnvelope,
} from "@mark/shared";
import { buildResultView, type TaskResultView } from "../lib/taskResult";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  streaming?: boolean;
}

export type PanelId =
  | "messages"
  | "ops"
  | "workspace"
  | "tasks"
  | "agents"
  | "vault"
  | "logs"
  | "integrations"
  | "settings";

interface MarkState {
  orbState: OrbState;
  activeNav: string;
  messages: ChatMessage[];
  executionFeed: ExecutionFeedPayload[];
  agents: AgentStatusPayload[];
  tasks: TaskUpdatedPayload[];
  pendingApproval: ApprovalRequestPayload | null;
  metrics: MetricsSnapshotPayload | null;
  wsConnected: boolean;
  token: string | null;
  voiceEnabled: boolean;
  voiceRecording: boolean;
  voiceAmplitude: number;
  voiceSpeaking: boolean;
  voiceTranscript: string;
  voiceError: string | null;
  voiceSessionActive: boolean;
  selectedMemoryId: string | null;
  sessionId: string | null;
  showMessages: boolean;
  orbZoom: number;
  openPanel: PanelId | null;
  chatMode: "chat" | "task";
  taskNotification: {
    taskId: string;
    title: string;
    kind: TaskResultKind;
    preview: string;
    messageId?: string;
    content: string;
    status: "completed" | "failed";
    dismissed: boolean;
  } | null;
  taskResultView: TaskResultView | null;
  highlightMessageId: string | null;
  /** Tasks we already showed a completion toast for. */
  notifiedTaskIds: Set<string>;
  workspaceMode: WorkspaceMode;
  visualize: VisualizeOpenPayload | null;
  briefing: BriefingOpenPayload | null;
  camSkill: { active: boolean; objective: string } | null;
  /** Non-null while waiting on POST /chat (shown in UI). */
  chatLoadingLabel: string | null;
  /** Operations report MARK should use when answering in chat. */
  contextTaskId: string | null;

  setOrbState: (s: OrbState) => void;
  setActiveNav: (nav: string) => void;
  setToken: (t: string | null) => void;
  setWsConnected: (v: boolean) => void;
  setVoiceEnabled: (v: boolean) => void;
  setVoiceRecording: (v: boolean) => void;
  setVoiceAmplitude: (v: number) => void;
  setVoiceSpeaking: (v: boolean) => void;
  setVoiceTranscript: (v: string) => void;
  setVoiceError: (v: string | null) => void;
  setVoiceSessionActive: (v: boolean) => void;
  setSelectedMemoryId: (id: string | null) => void;
  setSessionId: (id: string | null) => void;
  setShowMessages: (v: boolean) => void;
  setOrbZoom: (z: number) => void;
  setOpenPanel: (panel: PanelId | null) => void;
  togglePanel: (panel: PanelId) => void;
  setChatMode: (mode: "chat" | "task") => void;
  setChatLoadingLabel: (label: string | null) => void;
  setContextTaskId: (id: string | null) => void;
  setMessages: (messages: ChatMessage[]) => void;
  setTasks: (tasks: TaskUpdatedPayload[]) => void;
  addMessage: (m: ChatMessage) => void;
  upsertMessage: (m: ChatMessage) => void;
  appendDelta: (messageId: string, delta: string) => void;
  startNewChat: () => void;
  pushFeed: (line: ExecutionFeedPayload) => void;
  setAgents: (agents: AgentStatusPayload[]) => void;
  updateTask: (task: TaskUpdatedPayload) => void;
  setApproval: (a: ApprovalRequestPayload | null) => void;
  setMetrics: (m: MetricsSnapshotPayload) => void;
  handleWsEvent: (event: WsEnvelope) => void;
  resetChat: () => void;
  notifyTaskComplete: (task: TaskUpdatedPayload) => void;
  dismissTaskNotification: () => void;
  openTaskResult: () => void;
  closeTaskResult: () => void;
  setHighlightMessageId: (id: string | null) => void;
  openVisualize: (payload: VisualizeOpenPayload) => void;
  openBriefing: (payload: BriefingOpenPayload) => void;
  openCamSkill: (payload: CamSkillOpenPayload) => void;
  closeWorkspace: () => void;
}

export const useMarkStore = create<MarkState>((set, get) => ({
  orbState: "idle",
  activeNav: "home",
  messages: [],
  executionFeed: [],
  agents: [],
  tasks: [],
  pendingApproval: null,
  metrics: null,
  wsConnected: false,
  token: null,
  voiceEnabled: true,
  voiceRecording: false,
  voiceAmplitude: 0,
  voiceSpeaking: false,
  voiceTranscript: "",
  voiceError: null,
  voiceSessionActive: false,
  selectedMemoryId: null,
  sessionId: null,
  showMessages: false,
  orbZoom: 1,
  openPanel: null,
  chatMode: "chat",
  taskNotification: null,
  taskResultView: null,
  highlightMessageId: null,
  notifiedTaskIds: new Set(),
  workspaceMode: "idle",
  visualize: null,
  briefing: null,
  camSkill: null,
  chatLoadingLabel: null,
  contextTaskId: null,

  setOrbState: (orbState) => set({ orbState }),
  setContextTaskId: (contextTaskId) => set({ contextTaskId }),
  setChatLoadingLabel: (chatLoadingLabel) => set({ chatLoadingLabel }),
  setActiveNav: (activeNav) => set({ activeNav }),
  setToken: (token) => set({ token }),
  setWsConnected: (wsConnected) => set({ wsConnected }),
  setVoiceEnabled: (voiceEnabled) => set({ voiceEnabled }),
  setVoiceRecording: (voiceRecording) => set({ voiceRecording }),
  setVoiceAmplitude: (voiceAmplitude) => set({ voiceAmplitude }),
  setVoiceSpeaking: (voiceSpeaking) => set({ voiceSpeaking }),
  setVoiceTranscript: (voiceTranscript) => set({ voiceTranscript }),
  setVoiceError: (voiceError) => set({ voiceError }),
  setVoiceSessionActive: (voiceSessionActive) => set({ voiceSessionActive }),
  setSelectedMemoryId: (selectedMemoryId) => set({ selectedMemoryId }),
  setSessionId: (sessionId) => set({ sessionId }),
  setShowMessages: (showMessages) => set({ showMessages }),
  setOrbZoom: (orbZoom) => set({ orbZoom: Math.min(1.5, Math.max(0.6, orbZoom)) }),
  setOpenPanel: (openPanel) => set({ openPanel }),
  togglePanel: (panel) =>
    set((s) => {
      if (s.workspaceMode !== "idle" && panel === "messages") {
        return { openPanel: null };
      }
      return { openPanel: s.openPanel === panel ? null : panel };
    }),
  setChatMode: (chatMode) => set({ chatMode }),
  setMessages: (messages) => set({ messages }),
  setTasks: (tasks) => set({ tasks }),
  addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
  upsertMessage: (m) =>
    set((s) => {
      const idx = s.messages.findIndex((x) => x.id === m.id);
      if (idx >= 0) {
        const messages = [...s.messages];
        messages[idx] = { ...messages[idx], ...m, streaming: false };
        return { messages };
      }
      return { messages: [...s.messages, m] };
    }),
  startNewChat: () => {
    localStorage.removeItem("mark_session_id");
    set({ sessionId: null, messages: [], chatMode: "chat", showMessages: false });
  },
  appendDelta: (messageId, delta) =>
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === messageId ? { ...m, content: m.content + delta, streaming: true } : m
      ),
    })),
  pushFeed: (line) =>
    set((s) => ({
      executionFeed: [...s.executionFeed.slice(-199), line],
    })),
  setAgents: (agents) => set({ agents }),
  updateTask: (task) =>
    set((s) => {
      const idx = s.tasks.findIndex((t) => t.task_id === task.task_id);
      const tasks = [...s.tasks];
      if (idx >= 0) tasks[idx] = task;
      else tasks.push(task);
      return { tasks };
    }),
  setApproval: (pendingApproval) => set({ pendingApproval }),
  setMetrics: (metrics) => set({ metrics }),
  resetChat: () => set({ messages: [], executionFeed: [] }),

  notifyTaskComplete: (task) => {
    if (task.task_id) {
      set({ contextTaskId: task.task_id });
    }
    const view = buildResultView(task);
    if (!view) return;
    const { notifiedTaskIds } = get();
    if (notifiedTaskIds.has(task.task_id)) return;

    if (view.messageId) {
      const msgs = get().messages;
      const existing = msgs.find((m) => m.id === view.messageId);
      if (!existing) {
        get().addMessage({
          id: view.messageId,
          role: "assistant",
          content: view.content,
        });
      } else if (!existing.content) {
        get().upsertMessage({
          id: view.messageId,
          role: "assistant",
          content: view.content,
        });
      }
    }

    const nextNotified = new Set(notifiedTaskIds);
    nextNotified.add(task.task_id);

    set({
      notifiedTaskIds: nextNotified,
      taskNotification: {
        taskId: view.taskId,
        title: view.title,
        kind: view.kind,
        preview: view.preview,
        messageId: view.messageId,
        content: view.content,
        status: view.status,
        dismissed: false,
      },
    });
  },

  dismissTaskNotification: () =>
    set((s) =>
      s.taskNotification
        ? { taskNotification: { ...s.taskNotification, dismissed: true } }
        : {}
    ),

  openTaskResult: () => {
    const n = get().taskNotification;
    if (!n) return;
    const view: TaskResultView = {
      taskId: n.taskId,
      title: n.title,
      status: n.status,
      kind: n.kind,
      preview: n.preview,
      messageId: n.messageId,
      content: n.content,
    };
    const keepWorkspace = get().workspaceMode !== "idle";
    set({
      taskResultView: view,
      highlightMessageId: n.messageId ?? null,
      contextTaskId: n.taskId,
      showMessages: !keepWorkspace,
      openPanel: keepWorkspace ? null : "messages",
      taskNotification: { ...n, dismissed: true },
    });
    if (n.messageId) {
      window.setTimeout(() => {
        document
          .getElementById(`mark-msg-${n.messageId}`)
          ?.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 350);
    }
  },

  closeTaskResult: () => set({ taskResultView: null, highlightMessageId: null }),

  setHighlightMessageId: (highlightMessageId) => set({ highlightMessageId }),

  openVisualize: (payload) =>
    set({
      workspaceMode: "visualize",
      visualize: payload,
      briefing: null,
      camSkill: null,
      openPanel: null,
      showMessages: false,
    }),

  openBriefing: (payload) =>
    set({
      workspaceMode: "briefing",
      briefing: payload,
      visualize: null,
      camSkill: null,
      openPanel: null,
      showMessages: false,
    }),

  openCamSkill: (payload) =>
    set({
      workspaceMode: "cam",
      camSkill: { active: true, objective: payload.objective },
      visualize: null,
      briefing: null,
      openPanel: null,
      showMessages: false,
    }),

  closeWorkspace: () =>
    set({
      workspaceMode: "idle",
      visualize: null,
      briefing: null,
      camSkill: null,
    }),

  handleWsEvent: (event) => {
    const { type, payload } = event;
    switch (type) {
      case "chat.delta": {
        const p = payload as { message_id: string; delta: string };
        const msgs = get().messages;
        if (!msgs.find((m) => m.id === p.message_id)) {
          get().addMessage({
            id: p.message_id,
            role: "assistant",
            content: p.delta,
            streaming: true,
          });
        } else {
          get().appendDelta(p.message_id, p.delta);
        }
        get().setOrbState("thinking");
        break;
      }
      case "chat.message": {
        const p = payload as { message_id: string; role: "user" | "assistant"; content: string };
        const msgs = get().messages;
        const existing = msgs.find((m) => m.id === p.message_id);
        if (existing) {
          set({
            messages: msgs.map((m) =>
              m.id === p.message_id ? { ...m, content: p.content, streaming: false } : m
            ),
          });
        } else if (p.role === "user" && msgs.some((m) => m.id === p.message_id)) {
          /* client already added optimistic user bubble */
        } else {
          get().addMessage({ id: p.message_id, role: p.role, content: p.content });
        }
        if (p.role === "assistant") {
          const extra = payload as {
            speak?: boolean;
            task_id?: string;
            result_kind?: TaskResultKind;
          };
          const speak = extra.speak !== false;
          const intent = useMarkStore.getState().chatMode;
          const ws = get().workspaceMode;
          const voiceOn = get().voiceSessionActive || get().voiceSpeaking;
          if (!voiceOn && ws === "idle") {
            get().setOrbState(intent === "task" ? "executing" : "idle");
          }
          window.dispatchEvent(
            new CustomEvent("mark:assistant-message", {
              detail: { content: p.content, speak, message_id: p.message_id },
            })
          );
        }
        break;
      }
      case "task.updated": {
        const p = payload as TaskUpdatedPayload;
        get().updateTask(p);
        if (p.status === "completed" || p.status === "failed") {
          get().setOrbState("idle");
          if (p.result_preview || p.result_content || p.result_kind) {
            get().notifyTaskComplete(p);
          }
        }
        break;
      }
      case "execution.feed":
        get().pushFeed(payload as ExecutionFeedPayload);
        get().setOrbState("executing");
        break;
      case "agent.status": {
        const p = payload as AgentStatusPayload;
        const agents = [...get().agents];
        const i = agents.findIndex((a) => a.agent_id === p.agent_id);
        if (i >= 0) agents[i] = p;
        else agents.push(p);
        get().setAgents(agents);
        break;
      }
      case "approval.request":
        get().setApproval(payload as ApprovalRequestPayload);
        break;
      case "metrics.snapshot":
        get().setMetrics(payload as MetricsSnapshotPayload);
        break;
      case "voice.transcript": {
        const p = payload as { text: string; final: boolean };
        if (p.final) get().setOrbState("thinking");
        else get().setOrbState("listening");
        break;
      }
      case "chat.intent": {
        const p = payload as { intent: "chat" | "task" };
        get().setChatMode(p.intent);
        if (p.intent === "task") get().setOrbState("executing");
        break;
      }
      case "voice.audio": {
        const p = payload as { chunk: string; format: string; done?: boolean };
        window.dispatchEvent(new CustomEvent("mark:voice-audio", { detail: p }));
        if (p.done) get().setVoiceSpeaking(false);
        else get().setVoiceSpeaking(true);
        break;
      }
      case "visualize.open":
        get().openVisualize(payload as VisualizeOpenPayload);
        break;
      case "visualize.close":
        if (get().workspaceMode === "visualize") get().closeWorkspace();
        break;
      case "briefing.open":
        get().openBriefing(payload as BriefingOpenPayload);
        break;
      case "skill.cam.open":
        get().openCamSkill(payload as CamSkillOpenPayload);
        get().setOrbState("executing");
        break;
      case "skill.cam.close":
        if (get().workspaceMode === "cam") get().closeWorkspace();
        break;
      default:
        break;
    }
  },
}));
