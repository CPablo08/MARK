import { AnimatePresence, motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import { useMarkStore } from "../../store/markStore";
import { extractImageUrls, extractLinks, kindLabel } from "../../lib/taskResult";

export function TaskResultViewer() {
  const view = useMarkStore((s) => s.taskResultView);
  const closeTaskResult = useMarkStore((s) => s.closeTaskResult);

  const links = view ? extractLinks(view.content) : [];
  const images = view ? extractImageUrls(view.content) : [];

  return (
    <AnimatePresence>
      {view && (
        <>
          <motion.button
            type="button"
            className="mark-result-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeTaskResult}
            aria-label="Close result"
          />
          <motion.div
            className="mark-result-sheet"
            role="dialog"
            aria-labelledby="mark-result-title"
            initial={{ y: "100%", opacity: 0.95 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: "100%", opacity: 0.95 }}
            transition={{ type: "spring", damping: 28, stiffness: 320 }}
          >
            <header className="mark-result-header">
              <motion.div layout className="min-w-0 flex-1">
                <p className="mark-result-kind">{kindLabel(view.kind)}</p>
                <h2 id="mark-result-title" className="mark-result-title">
                  {view.title}
                </h2>
                <p className="mark-result-hint text-sm opacity-70 mt-1">
                  Ask MARK in chat or voice — e.g. &quot;What did you find?&quot; or &quot;Summarize
                  this report&quot; — and he&apos;ll answer from this report.
                </p>
              </motion.div>
              <button
                type="button"
                className="mark-panel-close"
                onClick={closeTaskResult}
                aria-label="Close"
              >
                ✕
              </button>
            </header>

            <div className="mark-result-body">
              {images.length > 0 && (
                <section className="mark-result-section">
                  <h3 className="mark-result-section-title">Images</h3>
                  <motion.div layout className="mark-result-images">
                    {images.map((src) => (
                      <a
                        key={src}
                        href={src}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mark-result-image-wrap"
                      >
                        <img src={src} alt="" className="mark-result-image" loading="lazy" />
                      </a>
                    ))}
                  </motion.div>
                </section>
              )}

              {links.length > 0 && (
                <section className="mark-result-section">
                  <h3 className="mark-result-section-title">Links</h3>
                  <ul className="mark-result-links">
                    {links.map((url) => (
                      <li key={url}>
                        <a
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mark-result-link"
                        >
                          {hostname(url)}
                        </a>
                        <span className="mark-result-link-url">{url}</span>
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              <section className="mark-result-section mark-result-markdown">
                <h3 className="mark-result-section-title">Full result</h3>
                <div className="prose prose-invert prose-sm max-w-none prose-p:my-2 prose-headings:text-gray-200 prose-a:text-accent-highlight">
                  <ReactMarkdown>{view.content}</ReactMarkdown>
                </div>
              </section>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function hostname(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url.slice(0, 48);
  }
}
