import { useMarkQueries } from "../../hooks/useMarkQuery";

export function IntegrationsPanelContent() {
  const { integrations } = useMarkQueries();

  if (integrations.isLoading) return <p className="text-sm text-muted">Loading…</p>;
  if (integrations.error) return <p className="text-sm text-red-400">{integrations.error.message}</p>;

  return (
    <ul className="space-y-2">
      {(integrations.data ?? []).map((i) => (
        <li
          key={i.id}
          className="flex items-center justify-between p-3 rounded-lg bg-surface border border-border/60"
        >
          <div>
            <p className="text-sm text-gray-200">{i.name}</p>
            <p className="text-[10px] text-muted uppercase">{i.type}</p>
          </div>
          <span
            className={`text-[10px] px-2 py-0.5 rounded ${
              i.enabled ? "bg-emerald-500/15 text-emerald-400" : "bg-gray-500/15 text-gray-500"
            }`}
          >
            {i.enabled ? "On" : "Off"}
          </span>
        </li>
      ))}
    </ul>
  );
}
