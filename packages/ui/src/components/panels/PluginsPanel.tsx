import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { useMarkStore } from "../../store/markStore";

export function PluginsPanel() {
  const token = useMarkStore((s) => s.token);
  const qc = useQueryClient();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: "", command: "npx", args: "", enabled: true });

  const { data, isLoading, error } = useQuery({
    queryKey: ["plugins-catalog", token],
    queryFn: () => api.pluginsCatalog(token!),
    enabled: !!token,
  });

  const refresh = async () => {
    await qc.invalidateQueries({ queryKey: ["plugins-catalog"] });
    await qc.invalidateQueries({ queryKey: ["integrations"] });
  };

  const toggle = async (id: string, enabled: boolean) => {
    if (!token) return;
    await api.patchIntegration(token, id, enabled);
    await refresh();
  };

  const startEdit = (id: string) => {
    const item = data?.integrations.find((i) => i.id === id);
    if (!item) return;
    const cfg = item.config as { command?: string; args?: string[] };
    setForm({
      name: item.name,
      command: cfg.command ?? "npx",
      args: Array.isArray(cfg.args) ? cfg.args.join(" ") : "",
      enabled: item.enabled,
    });
    setEditingId(id);
    setShowAdd(false);
  };

  const savePlugin = async () => {
    if (!token || !form.name.trim()) return;
    const config = {
      command: form.command.trim() || "npx",
      args: form.args.trim() ? form.args.trim().split(/\s+/) : [],
    };
    if (editingId) {
      await api.updateIntegration(token, editingId, {
        name: form.name.trim(),
        enabled: form.enabled,
        config,
      });
    } else {
      await api.createIntegration(token, {
        name: form.name.trim(),
        type: "mcp",
        enabled: form.enabled,
        config,
      });
    }
    setEditingId(null);
    setShowAdd(false);
    setForm({ name: "", command: "npx", args: "", enabled: true });
    await refresh();
  };

  const remove = async (id: string) => {
    if (!token || !confirm("Remove this plugin?")) return;
    await api.deleteIntegration(token, id);
    await refresh();
  };

  if (isLoading) return <p className="text-sm text-muted">Loading plugins…</p>;
  if (error) return <p className="text-sm text-red-400">{error.message}</p>;
  if (!data) return null;

  const formOpen = showAdd || !!editingId;

  return (
    <div className="space-y-5">
      <section>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-[10px] uppercase tracking-wider text-muted">Plugins</h3>
          <button
            type="button"
            className="text-[10px] text-accent uppercase tracking-wide"
            onClick={() => {
              setShowAdd(!showAdd);
              setEditingId(null);
              setForm({ name: "", command: "npx", args: "", enabled: true });
            }}
          >
            {showAdd ? "Cancel" : "+ Add"}
          </button>
        </div>
        <p className="text-[11px] text-muted mb-3 leading-relaxed">
          <strong>Visualize</strong> — HTML/charts in the center panel (
          <span className="font-mono text-gray-500">visualize</span>).{" "}
          <strong>Cam</strong> — live camera + object detection (
          <span className="font-mono text-gray-500">cam</span>,{" "}
          <span className="font-mono text-gray-500">cam_analyze</span>). Built-in{" "}
          <span className="font-mono text-gray-500">web_search</span> /{" "}
          <span className="font-mono text-gray-500">browse_url</span> need no MCP. MCP tools:{" "}
          <span className="font-mono text-gray-500">server__tool</span>.
        </p>
        {formOpen && (
          <div className="mb-3 p-3 rounded-lg border border-border bg-surface/60 space-y-2">
            <input
              placeholder="Plugin name"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              className="w-full text-xs bg-matte border border-border rounded px-2 py-1.5 text-gray-300"
            />
            <input
              placeholder="Command (npx)"
              value={form.command}
              onChange={(e) => setForm((f) => ({ ...f, command: e.target.value }))}
              className="w-full text-xs bg-matte border border-border rounded px-2 py-1.5 text-gray-300"
            />
            <input
              placeholder="Args (space-separated)"
              value={form.args}
              onChange={(e) => setForm((f) => ({ ...f, args: e.target.value }))}
              className="w-full text-xs bg-matte border border-border rounded px-2 py-1.5 text-gray-300"
            />
            <label className="flex items-center gap-2 text-xs text-muted">
              <input
                type="checkbox"
                checked={form.enabled}
                onChange={(e) => setForm((f) => ({ ...f, enabled: e.target.checked }))}
              />
              Enabled
            </label>
            <button
              type="button"
              onClick={() => void savePlugin()}
              className="w-full py-1.5 text-xs rounded bg-accent/20 text-accent border border-accent/30"
            >
              {editingId ? "Update plugin" : "Create plugin"}
            </button>
          </div>
        )}
        <ul className="space-y-2">
          {data.integrations.map((i) => (
            <li key={i.id} className="p-3 rounded-lg bg-surface border border-border/60">
              <div className="flex justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-sm text-gray-200">{i.name}</p>
                  <p className="text-[10px] text-muted font-mono truncate">
                    {(i.config as { command?: string }).command}{" "}
                    {((i.config as { args?: string[] }).args ?? []).join(" ")}
                  </p>
                </div>
                <div className="flex gap-1 shrink-0 items-center">
                  <button type="button" onClick={() => startEdit(i.id)} className="text-[10px] text-muted px-1">
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => void toggle(i.id, !i.enabled)}
                    className={`text-[10px] uppercase px-2 py-0.5 rounded border ${
                      i.enabled ? "border-accent/30 text-accent" : "border-border text-muted"
                    }`}
                  >
                    {i.enabled ? "On" : "Off"}
                  </button>
                  <button type="button" onClick={() => void remove(i.id)} className="text-[10px] text-red-400 px-1">
                    Del
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h3 className="text-[10px] uppercase tracking-wider text-muted mb-2">Built-in tools</h3>
        <ul className="space-y-1.5">
          {data.builtin_tools.map((t) => (
            <li key={t.name} className="text-[11px] text-gray-400 py-1 border-b border-border/30">
              <span className="text-accent font-mono">{t.name}</span>
              <span className="text-muted"> — {t.description}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
