import { motion, AnimatePresence } from "framer-motion";
import { useMarkStore } from "../store/markStore";
import { api } from "../lib/api";

function PayloadPreview({ payload }: { payload: Record<string, unknown> }) {
  const command = payload.command as string | undefined;
  const to = payload.to as string | undefined;
  const subject = payload.subject as string | undefined;
  const body = payload.body as string | undefined;
  const cwd = payload.cwd as string | undefined;

  if (command) {
    return (
      <pre className="text-xs text-gray-400 bg-black/40 rounded-lg p-3 overflow-x-auto font-mono whitespace-pre-wrap break-all max-h-40">
        {cwd ? `cwd: ${cwd}\n\n` : ""}
        {command}
      </pre>
    );
  }
  if (to && subject !== undefined) {
    return (
      <motion.div layout className="text-xs text-gray-400 space-y-2 bg-black/40 rounded-lg p-3 max-h-48 overflow-y-auto">
        <p>
          <span className="text-muted">To:</span> {to}
        </p>
        <p>
          <span className="text-muted">Subject:</span> {subject}
        </p>
        <p className="whitespace-pre-wrap">{body}</p>
      </motion.div>
    );
  }
  if (to && body && !subject) {
    return (
      <motion.div layout className="text-xs text-gray-400 bg-black/40 rounded-lg p-3">
        <p>
          <span className="text-muted">To:</span> {to}
        </p>
        <p className="mt-2 whitespace-pre-wrap">{body}</p>
      </motion.div>
    );
  }
  return (
    <pre className="text-xs text-gray-500 bg-black/40 rounded-lg p-3 overflow-auto max-h-32">
      {JSON.stringify(payload, null, 2)}
    </pre>
  );
}

export function ApprovalDialog() {
  const pending = useMarkStore((s) => s.pendingApproval);
  const setApproval = useMarkStore((s) => s.setApproval);
  const token = useMarkStore((s) => s.token);

  const resolve = async (approved: boolean) => {
    if (!pending || !token) return;
    await api.approvals.resolve(token, pending.approval_id, approved);
    setApproval(null);
  };

  const actionLabel: Record<string, string> = {
    terminal: "Terminal command",
    email: "Send email",
    sms: "Send SMS",
    phone_call: "Phone call",
  };

  return (
    <AnimatePresence>
      {pending && (
        <motion.div
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/75"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div
            className="bg-surface border border-accent/30 rounded-xl p-6 max-w-lg w-full mx-4 shadow-2xl"
            initial={{ scale: 0.95, y: 10 }}
            animate={{ scale: 1, y: 0 }}
          >
            <p className="text-[10px] uppercase tracking-widest text-accent mb-1">
              Supervised action
            </p>
            <h2 className="text-lg font-semibold text-white mb-2">
              {actionLabel[pending.action] ?? pending.action}
            </h2>
            <p className="text-sm text-gray-300 mb-4 whitespace-pre-wrap">{pending.description}</p>
            {pending.payload && Object.keys(pending.payload).length > 0 && (
              <PayloadPreview payload={pending.payload} />
            )}
            <p className="text-[11px] text-muted mt-4 mb-4">
              MARK will not run this until you approve. Deny if anything looks wrong.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={() => resolve(false)}
                className="px-4 py-2 rounded-lg border border-border text-gray-400 hover:text-white text-sm"
              >
                Deny
              </button>
              <button
                type="button"
                onClick={() => resolve(true)}
                className="px-4 py-2 rounded-lg bg-accent/25 text-accent border border-accent/40 text-sm font-medium"
              >
                Approve
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
