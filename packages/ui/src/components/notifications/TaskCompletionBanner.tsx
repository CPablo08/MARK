import { AnimatePresence, motion } from "framer-motion";
import { useMarkStore } from "../../store/markStore";
import { kindIcon, kindLabel } from "../../lib/taskResult";

export function TaskCompletionBanner() {
  const notification = useMarkStore((s) => s.taskNotification);
  const dismissTaskNotification = useMarkStore((s) => s.dismissTaskNotification);
  const openTaskResult = useMarkStore((s) => s.openTaskResult);

  return (
    <AnimatePresence>
      {notification && !notification.dismissed && (
        <motion.div
          className="mark-task-banner"
          role="status"
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          transition={{ type: "spring", damping: 26, stiffness: 340 }}
        >
          <button
            type="button"
            className="mark-task-banner__main"
            onClick={() => openTaskResult()}
          >
            <span className="mark-task-banner__icon" aria-hidden>
              {kindIcon(notification.kind)}
            </span>
            <span className="mark-task-banner__text">
              <span className="mark-task-banner__label">
                {kindLabel(notification.kind)}
              </span>
              <span className="mark-task-banner__preview">{notification.preview}</span>
            </span>
            <span className="mark-task-banner__action">View</span>
          </button>
          <button
            type="button"
            className="mark-task-banner__close"
            onClick={(e) => {
              e.stopPropagation();
              dismissTaskNotification();
            }}
            aria-label="Dismiss"
          >
            ✕
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
