import type { TaskResultKind, TaskUpdatedPayload } from "@mark/shared";

export interface TaskResultView {
  taskId: string;
  title: string;
  status: "completed" | "failed";
  kind: TaskResultKind;
  preview: string;
  messageId?: string;
  content: string;
}

const KIND_LABEL: Record<TaskResultKind, string> = {
  research: "Research complete",
  search: "Search complete",
  image: "Image ready",
  link: "Result ready",
  code: "Build complete",
  report: "Task complete",
  error: "Task failed",
};

export function kindLabel(kind: TaskResultKind): string {
  return KIND_LABEL[kind] ?? "Task complete";
}

export function kindIcon(kind: TaskResultKind): string {
  switch (kind) {
    case "research":
    case "search":
      return "⌕";
    case "image":
      return "◫";
    case "link":
      return "↗";
    case "code":
      return "</>";
    case "error":
      return "!";
    default:
      return "✓";
  }
}

export function buildResultView(task: TaskUpdatedPayload): TaskResultView | null {
  if (task.status !== "completed" && task.status !== "failed") return null;
  const kind =
    task.result_kind ??
    (task.status === "failed" ? "error" : ("report" as TaskResultKind));
  const content =
    task.result_content ??
    task.result_preview ??
    (task.status === "failed" ? "Task failed." : "Task finished.");
  return {
    taskId: task.task_id,
    title: task.title,
    status: task.status as "completed" | "failed",
    kind,
    preview: task.result_preview ?? content.slice(0, 140),
    messageId: task.result_message_id,
    content,
  };
}

/** Extract http(s) links for link/search result cards. */
export function extractLinks(content: string, limit = 12): string[] {
  const found = content.match(/https?:\/\/[^\s\)\]>]+/g) ?? [];
  const seen = new Set<string>();
  const out: string[] = [];
  for (const raw of found) {
    const url = raw.replace(/[.,;]+$/, "");
    if (!seen.has(url)) {
      seen.add(url);
      out.push(url);
    }
    if (out.length >= limit) return out;
  }
  return out;
}

/** Markdown / raw image URLs in content. */
export function extractImageUrls(content: string, limit = 6): string[] {
  const urls: string[] = [];
  const md = content.matchAll(/!\[[^\]]*\]\((https?:\/\/[^)]+)\)/gi);
  for (const m of md) {
    if (!urls.includes(m[1])) urls.push(m[1]);
    if (urls.length >= limit) return urls;
  }
  const direct = content.matchAll(
    /https?:\/\/[^\s\)\]>]+\.(?:png|jpe?g|webp|gif)(?:\?[^\s\)]*)?/gi
  );
  for (const m of direct) {
    if (!urls.includes(m[0])) urls.push(m[0]);
    if (urls.length >= limit) return urls;
  }
  return urls;
}
