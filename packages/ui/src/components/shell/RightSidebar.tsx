import { motion } from "framer-motion";
import { useMarkStore } from "../../store/markStore";
import { useMarkQueries } from "../../hooks/useMarkQuery";

export function RightSidebar() {
  const agents = useMarkStore((s) => s.agents);
  const tasks = useMarkStore((s) => s.tasks);
  const { objectives } = useMarkQueries();

  return (
    <aside className="flex flex-col h-full w-full">
      <Section title="Active Agents">
        {agents.length === 0 ? (
          <Empty>No agents running</Empty>
        ) : (
          agents.map((a) => (
            <motion.div
              key={a.agent_id}
              layout
              className="flex items-center justify-between py-2 px-3 rounded-md bg-surface/60 border border-border/50 mb-1.5"
            >
              <span className="text-[13px] capitalize text-gray-300">{a.role}</span>
              <StatusDot status={a.status} />
            </motion.div>
          ))
        )}
      </Section>

      <Section title="Objectives">
        {(objectives.data ?? []).map((o) => (
          <div key={o.id} className="mb-3 px-1">
            <motion.div className="flex justify-between text-[11px] mb-1.5 gap-2">
              <span className="text-gray-300 truncate">{o.title}</span>
              <span className="text-accent tabular-nums shrink-0">{Math.round(o.progress)}%</span>
            </motion.div>
            <div className="h-[3px] bg-border/80 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-accent/60 to-accent"
                initial={{ width: 0 }}
                animate={{ width: `${o.progress}%` }}
                transition={{ duration: 0.6, ease: "easeOut" }}
              />
            </div>
          </div>
        ))}
      </Section>

      <Section title="Tasks">
        {tasks.length === 0 ? (
          <Empty>No active tasks</Empty>
        ) : (
          tasks.slice(0, 5).map((t) => (
            <div
              key={t.task_id}
              className="px-2 py-1.5 text-[11px] border-b border-border/30 last:border-0"
            >
              <span className="text-gray-300 block truncate">{t.title}</span>
              <span className="text-accent/80 uppercase text-[9px] tracking-wide">{t.status}</span>
            </div>
          ))
        )}
      </Section>

      <Section title="Notifications">
        <Empty>Awaiting events</Empty>
      </Section>
    </aside>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="p-4 border-b border-border/80">
      <h3 className="text-[9px] uppercase tracking-[0.18em] text-muted/90 mb-3 font-medium">
        {title}
      </h3>
      {children}
    </div>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="text-[11px] text-muted/70 px-1">{children}</p>;
}

function StatusDot({ status }: { status: string }) {
  const color =
    status === "running"
      ? "bg-accent shadow-[0_0_8px_rgba(58,86,122,0.55)]"
      : status === "error"
        ? "bg-red-400"
        : status === "completed"
          ? "bg-emerald-400"
          : "bg-gray-600";
  return <span className={`w-1.5 h-1.5 rounded-full ${color}`} />;
}
