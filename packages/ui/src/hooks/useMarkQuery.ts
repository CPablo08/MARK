import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { useMarkStore } from "../store/markStore";

export function useMarkQueries() {
  const token = useMarkStore((s) => s.token);

  const tasks = useQuery({
    queryKey: ["tasks", token],
    queryFn: () => api.tasks(token!),
    enabled: !!token,
  });

  const agents = useQuery({
    queryKey: ["agents", token],
    queryFn: () => api.agents(token!),
    enabled: !!token,
  });

  const memory = useQuery({
    queryKey: ["memory", token],
    queryFn: () => api.memory(token!),
    enabled: !!token,
  });

  const objectives = useQuery({
    queryKey: ["objectives", token],
    queryFn: () => api.objectives(token!),
    enabled: !!token,
  });

  const integrations = useQuery({
    queryKey: ["integrations", token],
    queryFn: () => api.integrations(token!),
    enabled: !!token,
  });

  const logs = useQuery({
    queryKey: ["logs", token],
    queryFn: () => api.logs(token!),
    enabled: !!token,
  });

  return { tasks, agents, memory, objectives, integrations, logs };
}
