import type {
  AgentRole,
  MemoryCategory,
  SafetyMode,
  TaskStatus,
} from "./events";

export interface User {
  id: string;
  email: string;
  safety_mode: SafetyMode;
  settings: Record<string, unknown>;
}

export interface Task {
  id: string;
  title: string;
  objective: string;
  status: TaskStatus;
  progress: number;
  parent_task_id?: string;
  created_at: string;
  updated_at: string;
}

export interface AgentInstance {
  id: string;
  role: AgentRole;
  status: string;
  task_id?: string;
  created_at: string;
}

export interface MemoryRecord {
  id: string;
  category: MemoryCategory;
  scope: string;
  content: string;
  project_id?: string;
  created_at: string;
}

export interface Objective {
  id: string;
  title: string;
  progress: number;
  status: string;
  target_metric?: string;
  current_value?: string;
}

export interface Integration {
  id: string;
  name: string;
  type: string;
  enabled: boolean;
  config: Record<string, unknown>;
}

export interface AuditLogEntry {
  id: string;
  action: string;
  actor: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
