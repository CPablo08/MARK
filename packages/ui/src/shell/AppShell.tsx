import { motion } from "framer-motion";
import { ApprovalDialog } from "../components/ApprovalDialog";
import { TaskCompletionBanner } from "../components/notifications/TaskCompletionBanner";
import { TaskResultViewer } from "../components/notifications/TaskResultViewer";
import { BottomBar } from "../components/shell/BottomBar";
import { SlidePanel } from "../components/shell/SlidePanel";
import { CollapsedChatDock } from "../components/workspace/CollapsedChatDock";
import { VoiceOrbDock } from "../components/orb/VoiceOrbDock";
import { HomePage } from "../pages/HomePage";

export function AppShell() {
  return (
    <motion.div className="mark-shell">
      <TaskCompletionBanner />
      <main className="mark-main">
        <HomePage />
        <SlidePanel />
      </main>
      <CollapsedChatDock />
      <VoiceOrbDock />
      <BottomBar />
      <ApprovalDialog />
      <TaskResultViewer />
    </motion.div>
  );
}
