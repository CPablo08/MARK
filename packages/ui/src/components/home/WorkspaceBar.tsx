import { useWorkspaces } from "../../hooks/useWorkspaces";
import { useMarkStore } from "../../store/markStore";

export function WorkspaceBar() {
  const messages = useMarkStore((s) => s.messages);
  const sessionId = useMarkStore((s) => s.sessionId);
  const resetChat = useMarkStore((s) => s.resetChat);
  const setSessionId = useMarkStore((s) => s.setSessionId);
  const addMessage = useMarkStore((s) => s.addMessage);

  const { workspaces, active, toast, select, createNew, save, remove, clearToast } = useWorkspaces(
    messages,
    sessionId,
    (ws) => {
      resetChat();
      for (const m of ws.messages) addMessage(m);
      setSessionId(ws.sessionId);
    }
  );

  return (
    <>
      <div className="mark-float-panel mark-workspace-bar">
        <div className="flex flex-wrap items-center gap-2">
          <select
            className="mark-select flex-1 min-w-[140px]"
            value={active?.id ?? ""}
            onChange={(e) => select(e.target.value)}
          >
            {workspaces.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>
          <button type="button" className="mark-btn mark-btn--primary" onClick={createNew}>
            New
          </button>
          <button type="button" className="mark-btn" onClick={save}>
            Save
          </button>
          <button type="button" className="mark-btn mark-btn--danger" onClick={remove}>
            Delete
          </button>
        </div>
        <div className="mark-add-row">
          <span className="text-[9px] uppercase tracking-wider text-muted mr-1">Add</span>
          {["Text", "Idea", "Prompt", "Link"].map((label) => (
            <button
              key={label}
              type="button"
              className="mark-chip"
              onClick={() => {
                const input = document.getElementById("mark-command-input") as HTMLInputElement;
                if (input) {
                  input.value = `[${label}] `;
                  input.focus();
                }
              }}
            >
              + {label}
            </button>
          ))}
        </div>
      </div>
      {toast && (
        <div className="mark-toast">
          <span>{toast}</span>
          <button type="button" onClick={clearToast} className="mark-toast-dismiss">
            Dismiss
          </button>
        </div>
      )}
    </>
  );
}
