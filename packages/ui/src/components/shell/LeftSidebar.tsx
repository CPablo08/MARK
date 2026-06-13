import { motion } from "framer-motion";
import { useMarkStore } from "../../store/markStore";

const NAV = [
  { id: "home", label: "Home", icon: "◆" },
  { id: "tasks", label: "Tasks", icon: "▸" },
  { id: "agents", label: "Agents", icon: "◎" },
  { id: "memory", label: "Vault", icon: "⬡" },
  { id: "research", label: "Research", icon: "⌕" },
  { id: "automation", label: "Automation", icon: "⟳" },
  { id: "logs", label: "Logs", icon: "≡" },
  { id: "integrations", label: "Integrations", icon: "⎔" },
  { id: "settings", label: "Settings", icon: "⚙" },
];

export function LeftSidebar() {
  const activeNav = useMarkStore((s) => s.activeNav);
  const setActiveNav = useMarkStore((s) => s.setActiveNav);
  const metrics = useMarkStore((s) => s.metrics);
  const wsConnected = useMarkStore((s) => s.wsConnected);

  return (
    <aside className="flex flex-col h-full w-full">
      <div className="px-5 py-5 border-b border-border">
        <div className="flex items-center gap-2.5">
          <motion.span
            className="w-2 h-2 rounded-full bg-accent shrink-0"
            animate={{ opacity: wsConnected ? [1, 0.35, 1] : 0.25 }}
            transition={{ repeat: Infinity, duration: 2.2 }}
          />
          <span className="text-[15px] font-semibold tracking-tight text-accent">MARK</span>
        </div>
        <p className="text-[9px] text-muted mt-1.5 uppercase tracking-[0.2em] leading-relaxed">
          Machine Augmented Reasoning
        </p>
      </div>

      <nav className="flex-1 py-2 overflow-y-auto">
        {NAV.map((item) => {
          const active = activeNav === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => setActiveNav(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-2.5 text-[13px] transition-all ${
                active
                  ? "text-accent bg-accent/5 border-r-2 border-accent"
                  : "text-gray-500 hover:text-gray-200 hover:bg-white/[0.03]"
              }`}
            >
              <span className={`text-[10px] ${active ? "text-accent" : "text-gray-600"}`}>
                {item.icon}
              </span>
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="p-4 border-t border-border space-y-2.5 text-[11px] text-muted">
        <MetricRow label="Agents" value={String(metrics?.active_agents ?? 0)} highlight />
        <MetricRow label="Queue" value={String(metrics?.queue_depth ?? 0)} />
        <MetricRow label="Tokens" value={metrics?.tokens_used?.toLocaleString() ?? "—"} />
        <MetricRow
          label="Health"
          value={metrics?.system_health ?? "—"}
          valueClass={
            metrics?.system_health === "healthy"
              ? "text-emerald-400"
              : metrics?.system_health === "degraded"
                ? "text-amber-400"
                : "text-gray-500"
          }
        />
      </div>
    </aside>
  );
}

function MetricRow({
  label,
  value,
  highlight,
  valueClass = "",
}: {
  label: string;
  value: string;
  highlight?: boolean;
  valueClass?: string;
}) {
  return (
    <div className="flex justify-between items-center">
      <span>{label}</span>
      <span className={highlight ? "text-accent font-medium tabular-nums" : `tabular-nums ${valueClass}`}>
        {value}
      </span>
    </div>
  );
}
