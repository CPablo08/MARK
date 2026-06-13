export type WsEventType =
  | "chat.delta"
  | "chat.message"
  | "chat.intent"
  | "task.updated"
  | "execution.feed"
  | "agent.status"
  | "approval.request"
  | "approval.resolve"
  | "metrics.snapshot"
  | "voice.audio"
  | "voice.transcript"
  | "voice.cancel"
  | "visualize.open"
  | "visualize.close"
  | "briefing.open"
  | "briefing.close"
  | "skill.cam.open"
  | "skill.cam.close"
  | "ping"
  | "pong";

export type WorkspaceMode = "idle" | "visualize" | "cam" | "briefing";

export interface BriefingSource {
  title: string;
  url: string;
  snippet?: string;
}

export interface BriefingImage {
  url: string;
  thumb_url?: string;
  title?: string;
  source_url?: string;
}

export interface BriefingMarket {
  symbol?: string;
  name?: string;
  price?: number;
  currency?: string;
  change?: number;
  change_pct?: number;
  as_of?: string;
  market_state?: string;
  chart_url?: string;
  error?: string;
}

export type BriefingKind = "research" | "images" | "market" | "mixed";

export interface BriefingOpenPayload {
  id: string;
  query: string;
  title: string;
  summary: string;
  kind?: BriefingKind;
  image_url?: string | null;
  image_source?: string | null;
  images?: BriefingImage[];
  facts?: string[];
  sources?: BriefingSource[];
  market?: BriefingMarket | null;
}

export interface VisualizeOpenPayload {
  id: string;
  title: string;
  html: string;
  description?: string;
}

export interface CamSkillOpenPayload {
  objective: string;
}

export interface WsEnvelope<T = unknown> {
  type: WsEventType;
  payload: T;
  timestamp?: string;
  session_id?: string;
  task_id?: string;
}

export interface ChatDeltaPayload {
  message_id: string;
  delta: string;
}

export interface ChatMessagePayload {
  message_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  speak?: boolean;
}

export interface ChatIntentPayload {
  intent: "chat" | "task";
  session_id?: string;
}

export type TaskResultKind =
  | "research"
  | "search"
  | "image"
  | "link"
  | "code"
  | "report"
  | "error";

export interface TaskUpdatedPayload {
  task_id: string;
  title: string;
  status: TaskStatus;
  progress: number;
  objective?: string;
  result_message_id?: string;
  result_kind?: TaskResultKind;
  result_preview?: string;
  result_content?: string;
}

export type TaskStatus =
  | "pending"
  | "queued"
  | "running"
  | "awaiting_approval"
  | "completed"
  | "failed"
  | "cancelled";

export interface ExecutionFeedPayload {
  task_id?: string;
  line: string;
  level?: "info" | "warn" | "error";
}

export interface AgentStatusPayload {
  agent_id: string;
  role: AgentRole;
  status: "idle" | "running" | "error" | "completed";
  task_id?: string;
  message?: string;
}

export type AgentRole =
  | "commander"
  | "planner"
  | "research"
  | "coding"
  | "browser"
  | "verification"
  | "memory"
  | "finance";

export type SafetyMode = "safe" | "assisted" | "autonomous";

export type MemoryCategory =
  | "semantic"
  | "episodic"
  | "procedural"
  | "project"
  | "agent"
  | "credential";

export type OrbState = "idle" | "listening" | "thinking" | "executing";

export interface ApprovalRequestPayload {
  approval_id: string;
  task_id?: string;
  action: string;
  description: string;
  payload: Record<string, unknown>;
}

export interface MetricsSnapshotPayload {
  active_agents: number;
  queue_depth: number;
  tokens_used: number;
  system_health: "healthy" | "degraded" | "down";
}

export interface VoiceAudioPayload {
  chunk: string;
  format: "mp3" | "pcm";
  done?: boolean;
}

export interface VoiceTranscriptPayload {
  text: string;
  final: boolean;
}
