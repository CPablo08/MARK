import { motion, AnimatePresence } from "framer-motion";
import type { ExecutionFeedPayload } from "@mark/shared";

export function ExecutionFeed({ lines }: { lines: ExecutionFeedPayload[] }) {
  const visible = lines.slice(-10);

  return (
    <div className="px-5 py-3 h-full overflow-y-auto font-mono text-[11px]">
      <motion.div className="text-[9px] uppercase tracking-[0.15em] text-muted/80 mb-2">
        Live execution
      </motion.div>
      {visible.length === 0 ? (
        <p className="text-gray-600 text-[11px]">Standing by for task output…</p>
      ) : (
        <AnimatePresence mode="popLayout">
          {visible.map((line, i) => (
            <motion.div
              key={`${line.line}-${i}-${line.task_id ?? ""}`}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              className={`py-0.5 leading-relaxed ${
                line.level === "error"
                  ? "text-red-400/90"
                  : line.level === "warn"
                    ? "text-amber-400/90"
                    : "text-gray-500"
              }`}
            >
              <span className="text-accent/70 mr-2 select-none">›</span>
              {line.line}
            </motion.div>
          ))}
        </AnimatePresence>
      )}
    </div>
  );
}
