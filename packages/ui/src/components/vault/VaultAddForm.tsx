import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import type { MemoryCategory } from "@mark/shared";
import { api } from "../../lib/api";
import { useMarkStore } from "../../store/markStore";

const CATEGORIES: { id: MemoryCategory; label: string; hint: string }[] = [
  { id: "credential", label: "Login / credential", hint: "Site, username, password, API keys" },
  { id: "semantic", label: "Fact / knowledge", hint: "Preferences, definitions, reference info" },
  { id: "episodic", label: "Event / chat", hint: "Conversations and notable events" },
  { id: "procedural", label: "How-to", hint: "Workflows and procedures" },
  { id: "project", label: "Project", hint: "Project-specific notes" },
  { id: "agent", label: "Agent", hint: "Agent behavior and heuristics" },
];

export function VaultAddForm() {
  const token = useMarkStore((s) => s.token);
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState<MemoryCategory>("credential");
  const [label, setLabel] = useState("");
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    if (!token || !content.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const body =
        category === "credential" && label.trim()
          ? `${label.trim()}\n${content.trim()}`
          : content.trim();
      await api.createMemory(token, {
        category,
        content: body,
        scope: "vault",
        label: label.trim() || undefined,
      });
      setContent("");
      setLabel("");
      setOpen(false);
      await qc.invalidateQueries({ queryKey: ["memory-graph"] });
      await qc.invalidateQueries({ queryKey: ["memory"] });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const hint = CATEGORIES.find((c) => c.id === category)?.hint;

  return (
    <div className="mark-vault-add shrink-0 border-b border-border bg-surface/40">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-white/[0.02]"
        aria-expanded={open}
      >
        <span className="text-[10px] uppercase tracking-wider text-muted">Add to vault</span>
        <span className="text-muted text-xs" aria-hidden>
          {open ? "▾" : "▸"}
        </span>
      </button>
      {open && (
        <div className="px-3 pb-3 space-y-2 border-t border-border/40">
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value as MemoryCategory)}
            className="w-full text-xs bg-matte border border-border rounded px-2 py-1.5 text-gray-300"
          >
            {CATEGORIES.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
          {category === "credential" && (
            <input
              type="text"
              placeholder="Label (e.g. GitHub, AWS)…"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              className="w-full text-xs bg-matte border border-border rounded px-2 py-1.5 text-gray-300"
            />
          )}
          <textarea
            placeholder={hint ?? "Content…"}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={3}
            className="w-full text-xs bg-matte border border-border rounded px-2 py-1.5 text-gray-300 resize-none"
          />
          {error && <p className="text-[11px] text-red-400">{error}</p>}
          <button
            type="button"
            disabled={saving || !content.trim()}
            onClick={() => void submit()}
            className="w-full py-1.5 rounded text-xs font-medium bg-accent/20 text-accent border border-accent/30 disabled:opacity-40"
          >
            {saving ? "Saving…" : "Save to vault"}
          </button>
        </div>
      )}
    </div>
  );
}
