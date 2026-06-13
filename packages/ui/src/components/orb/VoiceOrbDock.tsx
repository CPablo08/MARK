import { motion } from "framer-motion";
import { ParticleOrb } from "./ParticleOrb";
import { useMarkStore } from "../../store/markStore";

/** Corner orb during voice — reacts to mic level and MARK state without glitching the hero orb. */
export function VoiceOrbDock() {
  const voiceSessionActive = useMarkStore((s) => s.voiceSessionActive);
  const voiceSpeaking = useMarkStore((s) => s.voiceSpeaking);
  const voiceRecording = useMarkStore((s) => s.voiceRecording);
  const orbState = useMarkStore((s) => s.orbState);
  const voiceAmplitude = useMarkStore((s) => s.voiceAmplitude);

  if (!voiceSessionActive && !voiceSpeaking && !voiceRecording) return null;

  const state =
    voiceSpeaking ? "thinking" : voiceRecording ? "listening" : orbState;

  return (
    <motion.div
      className="mark-voice-orb-dock"
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.85 }}
      aria-hidden
    >
      <div
        className="mark-voice-orb-dock__glow"
        style={{
          opacity: 0.35 + voiceAmplitude * 0.55,
          transform: `scale(${1 + voiceAmplitude * 0.25})`,
        }}
      />
      <div className="mark-voice-orb-dock__orb">
        <ParticleOrb state={state} amplitude={voiceAmplitude} compact />
      </div>
    </motion.div>
  );
}
