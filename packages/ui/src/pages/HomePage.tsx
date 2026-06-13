import { motion } from "framer-motion";
import { ParticleOrb } from "../components/orb/ParticleOrb";
import { ExecutionFeed } from "../components/chat/ExecutionFeed";
import { DotGridBackground } from "../components/home/DotGridBackground";
import { HomeClock, HomeZoomControls } from "../components/home/HomeChrome";
import { WorkspaceStage } from "../components/workspace/WorkspaceStage";
import { useMarkStore } from "../store/markStore";

export function HomePage() {
  const orbState = useMarkStore((s) => s.orbState);
  const voiceAmplitude = useMarkStore((s) => s.voiceAmplitude);
  const executionFeed = useMarkStore((s) => s.executionFeed);
  const orbZoom = useMarkStore((s) => s.orbZoom);
  const workspaceMode = useMarkStore((s) => s.workspaceMode);
  const voiceSessionActive = useMarkStore((s) => s.voiceSessionActive);
  const workspaceActive = workspaceMode !== "idle";
  const dimOrbForWorkspace = workspaceActive && !voiceSessionActive;

  return (
    <motion.div className="mark-home" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <DotGridBackground />
      <div className="mark-dot-grid" aria-hidden />

      <HomeClock />
      <HomeZoomControls />

      <WorkspaceStage />

      {!voiceSessionActive && (
      <motion.div
        className={`mark-orb-zone mark-orb-zone--hero ${dimOrbForWorkspace ? "mark-orb-zone--dimmed" : ""}`}
        animate={{ opacity: dimOrbForWorkspace ? 0.35 : 1 }}
        transition={{ duration: 0.35 }}
      >
        <motion.div className="mark-orb-stage" style={{ transform: `scale(${orbZoom})` }}>
          <ParticleOrb state={orbState} amplitude={voiceAmplitude} />
        </motion.div>
        {!workspaceActive && (
          <div className="mark-orb-caption">
            <h1 className="mark-orb-title">MARK</h1>
            <p className="mark-orb-hint">
              Machine Augmented Reasoning and Knowledgebase
            </p>
          </div>
        )}
      </motion.div>
      )}

      {executionFeed.length > 0 && !workspaceActive && !voiceSessionActive && (
        <motion.div className="mark-feed-zone mark-feed-zone--float">
          <ExecutionFeed lines={executionFeed} />
        </motion.div>
      )}
    </motion.div>
  );
}
