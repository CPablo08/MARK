import type {
  AgentInstance,
  AuditLogEntry,
  AuthTokens,
  Integration,
  MemoryRecord,
  Objective,
  Task,
  User,
} from "@mark/shared";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

function headers(token?: string | null): HeadersInit {
  const h: HeadersInit = { "Content-Type": "application/json" };
  if (token) h["Authorization"] = `Bearer ${token}`;
  return h;
}

function parseErrorDetail(err: unknown): string {
  if (!err || typeof err !== "object") return "Request failed";
  const detail = (err as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => (typeof d === "object" && d && "msg" in d ? String(d.msg) : String(d))).join(", ");
  }
  return "Request failed";
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...headers(token), ...options.headers },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(parseErrorDetail(err));
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  base: API_BASE,
  wsUrl: (token: string) => {
    const u = new URL(API_BASE);
    u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
    return `${u.origin}/ws/v1?token=${encodeURIComponent(token)}`;
  },

  session: () => request<AuthTokens>("/auth/session"),

  me: (token: string) => request<User>("/auth/me", {}, token),

  tasks: (token: string) => request<Task[]>("/tasks", {}, token),

  taskFeed: (token: string, taskId: string) =>
    request<Array<{ line: string; level: string; created_at: string }>>(
      `/tasks/${taskId}/feed`,
      {},
      token
    ),

  taskResult: (token: string, taskId: string) =>
    request<{
      task_id: string;
      title: string;
      status: string;
      result_message_id?: string | null;
      result_kind?: string | null;
      result_preview?: string | null;
      result_content?: string | null;
    }>(`/tasks/${taskId}/result`, {}, token),

  createTask: (token: string, body: { title: string; objective: string }) =>
    request<Task>("/tasks", { method: "POST", body: JSON.stringify(body) }, token),

  agents: (token: string) => request<AgentInstance[]>("/agents", {}, token),

  memory: (token: string, category?: string) =>
    request<MemoryRecord[]>(
      `/memory${category ? `?category=${encodeURIComponent(category)}` : ""}`,
      {},
      token
    ),

  memoryGraph: (token: string) =>
    request<{
      nodes: Array<{
        id: string;
        label: string;
        category: string;
        color: string;
        size: number;
        content: string;
      }>;
      links: Array<{ source: string; target: string }>;
    }>("/memory/graph", {}, token),

  objectives: (token: string) => request<Objective[]>("/objectives", {}, token),

  integrations: (token: string) => request<Integration[]>("/integrations", {}, token),

  pluginsCatalog: (token: string) =>
    request<{
      integrations: Integration[];
      builtin_tools: Array<{ name: string; description: string; tags: string[]; source: string }>;
      mcp_tools: Array<{ name: string; description: string; tags: string[]; source: string }>;
    }>("/integrations/catalog", {}, token),

  patchIntegration: (token: string, id: string, enabled: boolean) =>
    request<Integration>(`/integrations/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ enabled }),
    }, token),

  createIntegration: (
    token: string,
    body: { name: string; type?: string; enabled?: boolean; config: Record<string, unknown> }
  ) =>
    request<Integration>("/integrations", { method: "POST", body: JSON.stringify(body) }, token),

  updateIntegration: (
    token: string,
    id: string,
    body: { name?: string; enabled?: boolean; config?: Record<string, unknown> }
  ) =>
    request<Integration>(`/integrations/${id}`, { method: "PUT", body: JSON.stringify(body) }, token),

  deleteIntegration: (token: string, id: string) =>
    request<{ ok: boolean }>(`/integrations/${id}`, { method: "DELETE" }, token),

  createMemory: (
    token: string,
    body: { category: string; content: string; scope?: string; label?: string }
  ) =>
    request<MemoryRecord>("/memory", { method: "POST", body: JSON.stringify(body) }, token),

  deleteMemory: (token: string, id: string) =>
    request<{ ok: boolean }>(`/memory/${id}`, { method: "DELETE" }, token),

  sessions: (token: string) =>
    request<
      Array<{
        id: string;
        title: string;
        created_at: string;
        updated_at: string;
        message_count: number;
      }>
    >("/sessions", {}, token),

  sessionMessages: (token: string, sessionId: string) =>
    request<Array<{ id: string; role: string; content: string; created_at: string }>>(
      `/sessions/${sessionId}/messages`,
      {},
      token
    ),

  logs: (token: string) => request<AuditLogEntry[]>("/logs", {}, token),

  approvals: {
    resolve: (token: string, id: string, approved: boolean) =>
      request<{ ok: boolean }>(
        `/approvals/${id}/resolve`,
        { method: "POST", body: JSON.stringify({ approved }) },
        token
      ),
  },

  chat: (
    token: string,
    body: {
      content: string;
      session_id?: string;
      new_chat?: boolean;
      for_voice?: boolean;
      client_message_id?: string;
      task_id?: string;
    }
  ) =>
    request<{
      session_id: string;
      task_id?: string | null;
      task?: {
        task_id: string;
        title: string;
        status: string;
        progress: number;
        objective: string;
      } | null;
      mode: string;
      intent: string;
      assistant_message_id?: string | null;
      assistant_content?: string | null;
      visualize?: {
        id: string;
        title: string;
        html: string;
        description?: string;
      } | null;
      briefing?: {
        id: string;
        query: string;
        title: string;
        summary: string;
        kind?: string;
        image_url?: string | null;
        image_source?: string | null;
        images?: {
          url: string;
          thumb_url?: string;
          title?: string;
          source_url?: string;
        }[];
        facts?: string[];
        sources?: { title: string; url: string; snippet?: string }[];
        market?: {
          symbol?: string;
          name?: string;
          price?: number;
          currency?: string;
          change?: number;
          change_pct?: number;
          as_of?: string;
          chart_url?: string;
          error?: string;
        } | null;
      } | null;
    }>(
      "/chat",
      { method: "POST", body: JSON.stringify(body) },
      token
    ),

  updateSettings: (token: string, body: { safety_mode?: string }) =>
    request<User>("/auth/settings", { method: "PATCH", body: JSON.stringify(body) }, token),

  camFrame: (
    token: string,
    body: {
      image_base64: string;
      width: number;
      height: number;
      detections: Array<{
        class: string;
        score: number;
        x?: number;
        y?: number;
        width?: number;
        height?: number;
      }>;
    }
  ) =>
    request<{ ok: boolean }>(
      "/skills/cam/frame",
      { method: "POST", body: JSON.stringify(body) },
      token
    ),

  camStatus: (token: string) =>
    request<{ has_frame: boolean; updated_at?: string; detection_count: number }>(
      "/skills/cam/status",
      {},
      token
    ),

  voice: {
    transcribe: (token: string, audioBase64: string, format = "webm") =>
      request<{ text: string; final: boolean }>(
        "/voice/transcribe",
        { method: "POST", body: JSON.stringify({ audio: audioBase64, format }) },
        token
      ),
    speak: (token: string, text: string) =>
      request<{ ok: boolean; audio?: string; format?: string; error?: string | null }>(
        "/voice/speak",
        { method: "POST", body: JSON.stringify({ text }) },
        token
      ),
  },
};
