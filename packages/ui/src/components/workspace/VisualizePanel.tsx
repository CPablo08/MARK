import { useState } from "react";
import { motion } from "framer-motion";
import { wrapVisualizationHtml } from "../../lib/visualizeHtml";
import { useMarkStore } from "../../store/markStore";

export function VisualizePanel() {
  const visualize = useMarkStore((s) => s.visualize);
  const closeWorkspace = useMarkStore((s) => s.closeWorkspace);
  const [tab, setTab] = useState<"preview" | "code">("preview");

  if (!visualize) return null;

  const srcDoc = wrapVisualizationHtml(visualize.html);

  return (
    <motion.div
      className="mark-center-panel"
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
    >
      <header className="mark-center-panel__header">
        <div className="min-w-0 flex-1">
          <p className="mark-center-panel__tag">Visualize</p>
          <h2 className="mark-center-panel__title">{visualize.title}</h2>
          {visualize.description && (
            <p className="mark-center-panel__desc">{visualize.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <div className="mark-center-tabs">
            <button
              type="button"
              className={tab === "preview" ? "mark-center-tabs__btn--active" : ""}
              onClick={() => setTab("preview")}
            >
              Preview
            </button>
            <button
              type="button"
              className={tab === "code" ? "mark-center-tabs__btn--active" : ""}
              onClick={() => setTab("code")}
            >
              Code
            </button>
          </div>
          <button
            type="button"
            className="mark-panel-close"
            onClick={closeWorkspace}
            aria-label="Close visualization"
          >
            ✕
          </button>
        </div>
      </header>
      <motion.div layout className="mark-center-panel__body mark-center-panel__body--artifact">
        {tab === "preview" ? (
          <iframe
            title={visualize.title}
            className="mark-visualize-frame"
            sandbox="allow-scripts allow-same-origin"
            srcDoc={srcDoc}
          />
        ) : (
          <pre className="mark-visualize-code">{visualize.html}</pre>
        )}
      </motion.div>
    </motion.div>
  );
}
