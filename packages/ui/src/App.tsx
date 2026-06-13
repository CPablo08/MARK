import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { AppShell } from "./shell/AppShell";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { MarkOrb } from "./components/orb/MarkOrb";
import { useMarkStore } from "./store/markStore";
import { useWebSocket } from "./hooks/useWebSocket";
import { useMarkBootstrap } from "./hooks/useMarkBootstrap";
import { useOpsSync } from "./hooks/useOpsSync";
import { useTaskCompletionPoll } from "./hooks/useTaskCompletionPoll";
import { api } from "./lib/api";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 10_000 },
  },
});

function BootScreen({ error }: { error?: string }) {
  return (
    <motion.div
      className="h-full flex flex-col items-center justify-center gap-4 bg-matte"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <div className="scale-50">
        <MarkOrb state="thinking" />
      </div>
      <p className="text-sm text-muted">{error ?? "Starting MARK…"}</p>
    </motion.div>
  );
}

export function MarkApp() {
  const token = useMarkStore((s) => s.token);
  const setToken = useMarkStore((s) => s.setToken);
  const [bootError, setBootError] = useState<string | null>(null);

  useWebSocket(token);
  useMarkBootstrap(token);
  useOpsSync(token);
  useTaskCompletionPoll(token);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const session = await api.session();
        if (!cancelled) setToken(session.access_token);
      } catch (e) {
        if (!cancelled) {
          setBootError(e instanceof Error ? e.message : "Could not reach MARK API");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [setToken]);

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <motion.div className="h-full w-full" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {token ? <AppShell /> : <BootScreen error={bootError ?? undefined} />}
        </motion.div>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
