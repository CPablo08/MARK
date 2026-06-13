import { motion } from "framer-motion";
import { useCamSkill } from "../../hooks/useCamSkill";
import { useMarkStore } from "../../store/markStore";

export function CamSkillPanel() {
  const cam = useMarkStore((s) => s.camSkill);
  const closeWorkspace = useMarkStore((s) => s.closeWorkspace);
  const active = !!cam?.active;

  const { videoRef, canvasRef, error, loading, detections, modelReady, stopCamera } =
    useCamSkill(active);

  if (!cam?.active) return null;

  return (
    <motion.div
      className="mark-center-panel mark-center-panel--cam"
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
    >
      <header className="mark-center-panel__header">
        <div className="min-w-0 flex-1">
          <p className="mark-center-panel__tag">Cam skill</p>
          <h2 className="mark-center-panel__title">Live camera + CV</h2>
          <p className="mark-center-panel__desc">{cam.objective}</p>
        </div>
        <button
          type="button"
          className="mark-panel-close"
          onClick={() => {
            stopCamera();
            closeWorkspace();
          }}
          aria-label="Close camera"
        >
          ✕
        </button>
      </header>
      <motion.div layout className="mark-center-panel__body mark-cam-body">
        {error && <p className="mark-cam-error">{error}</p>}
        {loading && !modelReady && (
          <p className="mark-cam-status">Loading object detection model…</p>
        )}
        <div className="mark-cam-viewport">
          <video ref={videoRef} className="mark-cam-video" playsInline muted />
          <canvas ref={canvasRef} className="mark-cam-overlay" />
        </div>
        <aside className="mark-cam-sidebar">
          <p className="text-[9px] uppercase tracking-wider text-muted mb-2">
            Detections {modelReady ? "" : "(loading…)"}
          </p>
          {detections.length === 0 ? (
            <p className="text-[11px] text-muted">Point the camera at objects…</p>
          ) : (
            <ul className="mark-cam-detections">
              {detections.slice(0, 12).map((d, i) => (
                <li key={`${d.class}-${i}`}>
                  <span className="text-gray-300">{d.class}</span>
                  <span className="text-muted tabular-nums">
                    {Math.round(d.score * 100)}%
                  </span>
                </li>
              ))}
            </ul>
          )}
          <p className="text-[10px] text-muted mt-3 leading-relaxed">
            Frames upload every ~2s for MARK to analyze with{" "}
            <code className="text-accent/80">cam_analyze</code>.
          </p>
        </aside>
      </motion.div>
    </motion.div>
  );
}
