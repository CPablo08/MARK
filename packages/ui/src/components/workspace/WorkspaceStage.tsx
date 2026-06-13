import { AnimatePresence, motion } from "framer-motion";
import { useMarkStore } from "../../store/markStore";
import { BriefingPanel } from "./BriefingPanel";
import { CamSkillPanel } from "./CamSkillPanel";
import { VisualizePanel } from "./VisualizePanel";

export function WorkspaceStage() {
  const mode = useMarkStore((s) => s.workspaceMode);

  if (mode === "idle") return null;

  return (
    <motion.div
      className="mark-workspace-stage mark-workspace-stage--active"
      aria-live="polite"
    >
      <AnimatePresence mode="wait">
        {mode === "visualize" && <VisualizePanel key="viz" />}
        {mode === "cam" && <CamSkillPanel key="cam" />}
        {mode === "briefing" && <BriefingPanel key="briefing" />}
      </AnimatePresence>
    </motion.div>
  );
}
