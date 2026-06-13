import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import type { SafetyMode } from "@mark/shared";
import { useMarkQueries } from "../hooks/useMarkQuery";
import { useMarkStore } from "../store/markStore";
import { api } from "../lib/api";

export function TasksPage() {
  const { tasks } = useMarkQueries();
  return (
    <PageShell title="Tasks">
      <DataList
        items={(tasks.data ?? []).map((t) => ({
          id: t.id,
          primary: t.title,
          secondary: `${t.status} · ${Math.round(t.progress)}%`,
        }))}
        loading={tasks.isLoading}
        error={tasks.error?.message}
      />
    </PageShell>
  );
}

export function AgentsPage() {
  const { agents } = useMarkQueries();
  const live = useMarkStore((s) => s.agents);
  return (
    <PageShell title="Agents">
      <DataList
        items={(agents.data ?? []).map((a) => ({
          id: a.id,
          primary: a.role,
          secondary: a.status,
        }))}
        loading={agents.isLoading}
        error={agents.error?.message}
      />
      {live.length > 0 && (
        <section className="mt-6">
          <h3 className="text-xs uppercase text-muted mb-2">Live</h3>
          {live.map((a) => (
            <motion.div
              key={a.agent_id}
              layout
              className="text-sm py-1 text-gray-400 flex justify-between"
            >
              <span className="capitalize">{a.role}</span>
              <span className="text-accent">{a.status}</span>
            </motion.div>
          ))}
        </section>
      )}
    </PageShell>
  );
}

export function MemoryPage() {
  const { memory } = useMarkQueries();
  return (
    <PageShell title="Memory">
      <DataList
        items={(memory.data ?? []).map((m) => ({
          id: m.id,
          primary: m.category,
          secondary: m.content.slice(0, 120),
        }))}
        loading={memory.isLoading}
        error={memory.error?.message}
      />
    </PageShell>
  );
}

export function LogsPage() {
  const { logs } = useMarkQueries();
  return (
    <PageShell title="Logs & Audit">
      <DataList
        items={(logs.data ?? []).map((l) => ({
          id: l.id,
          primary: l.action,
          secondary: new Date(l.created_at).toLocaleString(),
        }))}
        loading={logs.isLoading}
        error={logs.error?.message}
      />
    </PageShell>
  );
}

export function IntegrationsPage() {
  const { integrations } = useMarkQueries();
  return (
    <PageShell title="Integrations">
      <DataList
        items={(integrations.data ?? []).map((i) => ({
          id: i.id,
          primary: i.name,
          secondary: i.enabled ? "enabled" : "disabled",
        }))}
        loading={integrations.isLoading}
        error={integrations.error?.message}
      />
    </PageShell>
  );
}

export function SettingsPage() {
  const token = useMarkStore((s) => s.token);
  const setOrbState = useMarkStore((s) => s.setOrbState);
  const [safetyMode, setSafetyMode] = useState<SafetyMode>("assisted");
  const [saved, setSaved] = useState(false);

  const modes: SafetyMode[] = ["safe", "assisted", "autonomous"];

  useEffect(() => {
    if (!token) return;
    api.me(token).then((u) => setSafetyMode(u.safety_mode as SafetyMode)).catch(() => {});
  }, [token]);

  const applyMode = async (m: SafetyMode) => {
    if (!token) return;
    await api.updateSettings(token, { safety_mode: m });
    setSafetyMode(m);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <PageShell title="Settings">
      <motion.div className="space-y-6 max-w-lg" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <div>
          <h3 className="text-xs uppercase text-muted mb-3">Safety mode</h3>
          <div className="flex gap-2 flex-wrap">
            {modes.map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => applyMode(m)}
                className={`px-3 py-1.5 rounded border text-sm capitalize transition-colors ${
                  safetyMode === m
                    ? "border-accent text-accent bg-accent/10"
                    : "border-border text-gray-400 hover:border-accent/50"
                }`}
              >
                {m}
              </button>
            ))}
          </div>
          {saved && <p className="text-xs text-accent mt-2">Saved</p>}
        </div>
        <VoiceControls setOrbState={setOrbState} token={token} />
        <motion.div className="text-xs text-muted pt-4 border-t border-border space-y-2">
          <p className="text-gray-400">
            <strong className="text-gray-300">Supervised actions</strong> — terminal, email, SMS, and
            calls always show an Approve dialog (assisted mode). Configure SMTP and Twilio in{" "}
            <code className="text-accent/80">.env</code>.
          </p>
          <p>Personal install — no login required.</p>
          <p>API: {api.base}</p>
        </motion.div>
      </motion.div>
    </PageShell>
  );
}

function VoiceControls({
  token,
  setOrbState,
}: {
  token: string | null;
  setOrbState: (s: import("@mark/shared").OrbState) => void;
}) {
  return (
    <div>
      <h3 className="text-xs uppercase text-muted mb-3">Voice</h3>
      <p className="text-sm text-gray-500 mb-2">Hold to speak — streams via MARK voice API.</p>
      <button
        type="button"
        disabled={!token}
        onMouseDown={() => setOrbState("listening")}
        onMouseUp={() => setOrbState("idle")}
        onMouseLeave={() => setOrbState("idle")}
        className="px-4 py-2 rounded border border-accent/30 text-accent text-sm disabled:opacity-40"
      >
        Hold to speak
      </button>
    </div>
  );
}

function PageShell({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <motion.div
      className="p-8 overflow-y-auto h-full"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <h1 className="text-xl font-semibold text-white mb-6">{title}</h1>
      {children}
    </motion.div>
  );
}

function DataList({
  items,
  loading,
  error,
}: {
  items: { id: string; primary: string; secondary: string }[];
  loading: boolean;
  error?: string;
}) {
  if (loading) return <p className="text-muted text-sm">Loading...</p>;
  if (error) return <p className="text-red-400 text-sm">{error}</p>;
  if (items.length === 0) return <p className="text-muted text-sm">No records.</p>;
  return (
    <div className="space-y-2">
      {items.map((item) => (
        <motion.div
          key={item.id}
          layout
          className="p-3 rounded-lg bg-surface border border-border text-sm"
        >
          <div className="text-gray-200">{item.primary}</div>
          <div className="text-muted text-xs mt-1 truncate">{item.secondary}</div>
        </motion.div>
      ))}
    </div>
  );
}

export function StubPage({ title }: { title: string }) {
  return (
    <PageShell title={title}>
      <p className="text-muted text-sm">Module connected. Configure via MARK commander.</p>
    </PageShell>
  );
}
