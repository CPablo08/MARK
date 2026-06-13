import { motion } from "framer-motion";
import { useMarkStore } from "../../store/markStore";

const ACTIVE = new Set(["pending", "queued", "running", "awaiting_approval"]);
const TERMINAL = new Set(["completed", "failed", "cancelled"]);

export function OperationsPanel() {
  const agents = useMarkStore((s) => s.agents);
  const tasks = useMarkStore((s) => s.tasks);
  const executionFeed = useMarkStore((s) => s.executionFeed);
  const wsConnected = useMarkStore((s) => s.wsConnected);

  const activeTasks = tasks.filter((t) => ACTIVE.has(t.status));
  const recentDone = tasks
    .filter((t) => TERMINAL.has(t.status))
    .slice(0, 5);
  const runningAgents = agents.filter((a) => a.status === "running");

  return (
    <motion.div className="space-y-5" layout>
      <motion.div
        layout
        className="flex flex-wrap gap-3 text-[11px] text-muted"
      >
        <span>
          Agents: <strong className="text-gray-300">{runningAgents.length}</strong>
        </span>
        <span>
          Active: <strong className="text-gray-300">{activeTasks.length}</strong>
        </span>
        <span className={wsConnected ? "text-accent" : "text-amber-500/90"}>
          {wsConnected ? "Live" : "Polling"}
        </span>
      </motion.div>

      <Section title="Running agents">
        {runningAgents.length === 0 ? (
          <Empty>No agents running</Empty>
        ) : (
          runningAgents.map((a) => (
            <motion.div
              key={a.agent_id}
              layout
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center justify-between py-2 px-3 rounded-md bg-surface/60 border border-border/50 mb-1.5"
            >
              <span className="text-[13px] capitalize text-gray-300">{a.role}</span>
              <StatusDot status={a.status} />
            </motion.div>
          ))
        )}
      </Section>

      <Section title="Active tasks">
        {activeTasks.length === 0 ? (
          <Empty>No running tasks — ask MARK to research or build something</Empty>
        ) : (
          activeTasks.map((t) => (
            <TaskRow key={t.task_id} title={t.title} status={t.status} progress={t.progress} />
          ))
        )}
      </Section>

      {recentDone.length > 0 && (
        <Section title="Recently finished">
          {recentDone.map((t) => (
            <TaskRow
              key={t.task_id}
              title={t.title}
              status={t.status}
              progress={t.progress}
              dim
            />
          ))}
        </Section>
      )}

      <Section title="Execution feed">
        {executionFeed.length === 0 ? (
          <Empty>Waiting for task activity…</Empty>
        ) : (
          <ul className="max-h-48 overflow-y-auto space-y-1 pr-1">
            {executionFeed.slice(-24).map((line, i) => (
              <li
                key={`${line.task_id}-${i}-${line.line.slice(0, 24)}`}
                className={`text-[10px] font-mono leading-relaxed ${
                  line.level === "error" ? "text-red-400/90" : "text-gray-500"
                }`}
              >
                <span className="text-accent/60">›</span> {line.line}
              </li>
            ))}
          </ul>
        )}
      </Section>
    </motion.div>
  );
}

function TaskRow({
  title,
  status,
  progress,
  dim,
}: {
  title: string;
  status: string;
  progress: number;
  dim?: boolean;
}) {
  return (
    <div
      className={`px-2 py-2 text-[11px] border-b border-border/30 last:border-0 ${
        dim ? "opacity-70" : ""
      }`}
    >
      <span className="text-gray-300 block truncate">{title}</span>
      <motion.div
        className="h-[3px] bg-border/80 rounded-full overflow-hidden mt-2 mb-1"
        initial={false}
      >
        <motion.div
          className="h-full bg-gradient-to-r from-accent/50 to-accent"
          animate={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        />
      </motion.div>
      <motion.div layout className="flex justify-between mt-0.5">
        <span className="text-accent/80 uppercase text-[9px] tracking-wide">{status}</span>
        <span className="text-muted tabular-nums">{Math.round(progress)}%</span>
      </motion.div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <motion.div layout>
      <h3 className="text-[9px] uppercase tracking-[0.18em] text-muted/90 mb-2 font-medium">
        {title}
      </h3>
      {children}
    </motion.div>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="text-[11px] text-muted/70">{children}</p>;
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
