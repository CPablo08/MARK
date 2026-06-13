import { useState } from "react";
import { motion } from "framer-motion";
import { proxiedImageUrl } from "../../lib/mediaProxy";
import { useMarkStore } from "../../store/markStore";

function host(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export function BriefingPanel() {
  const briefing = useMarkStore((s) => s.briefing);
  const token = useMarkStore((s) => s.token);
  const closeWorkspace = useMarkStore((s) => s.closeWorkspace);
  const [lightbox, setLightbox] = useState<string | null>(null);

  if (!briefing) return null;

  const facts = briefing.facts ?? [];
  const sources = briefing.sources ?? [];
  const images = briefing.images ?? [];
  const kind = briefing.kind ?? "research";
  const market = briefing.market;
  const hero = proxiedImageUrl(briefing.image_url, token);

  return (
    <motion.div
      className="mark-center-panel mark-center-panel--briefing mark-center-panel--spotlight"
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
    >
      <header className="mark-center-panel__header">
        <motion.div layout className="min-w-0 flex-1">
          <p className="mark-center-panel__tag">
            {kind === "market" ? "Markets" : kind === "images" ? "Images" : "Research"}
          </p>
          <h2 className="mark-center-panel__title">{briefing.title}</h2>
          <p className="mark-center-panel__desc">Query: {briefing.query}</p>
        </motion.div>
        <button
          type="button"
          className="mark-panel-close"
          onClick={closeWorkspace}
          aria-label="Close research panel"
        >
          ✕
        </button>
      </header>

      <motion.div layout className="mark-briefing-body">
        {kind === "market" && market && !market.error && market.price != null && (
          <section className="mark-briefing-market">
            <p className="mark-briefing-market__price">
              {market.price.toLocaleString(undefined, { maximumFractionDigits: 2 })}{" "}
              <span className="mark-briefing-market__ccy">{market.currency ?? "USD"}</span>
            </p>
            {market.change != null && market.change_pct != null && (
              <p
                className={
                  market.change >= 0
                    ? "mark-briefing-market__change mark-briefing-market__change--up"
                    : "mark-briefing-market__change mark-briefing-market__change--down"
                }
              >
                {market.change >= 0 ? "+" : ""}
                {market.change.toFixed(2)} ({market.change_pct >= 0 ? "+" : ""}
                {market.change_pct.toFixed(2)}%)
              </p>
            )}
            {market.as_of && <p className="mark-briefing-market__asof">As of {market.as_of}</p>}
            {market.chart_url && (
              <a
                href={market.chart_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mark-briefing-market__chart"
              >
                View chart on Yahoo Finance
              </a>
            )}
          </section>
        )}

        {hero && (
          <figure className="mark-briefing-hero">
            <img
              src={hero}
              alt=""
              className="mark-briefing-hero__img"
              loading="lazy"
              onClick={() => setLightbox(briefing.image_url ?? null)}
            />
            {briefing.image_source && (
              <figcaption className="mark-briefing-hero__cap">
                Image: {briefing.image_source}
              </figcaption>
            )}
          </figure>
        )}

        {images.length > 0 && (
          <section className="mark-briefing-section">
            <h3 className="mark-briefing-section__title">
              {kind === "images" ? "Results" : "Related images"}
            </h3>
            <motion.div layout className="mark-briefing-grid">
              {images.map((img) => {
                const src = proxiedImageUrl(img.thumb_url || img.url, token);
                return (
                  <button
                    key={img.url}
                    type="button"
                    className="mark-briefing-grid__item"
                    onClick={() => setLightbox(img.url)}
                  >
                    <img src={src} alt={img.title || ""} loading="lazy" />
                    {img.title && <span className="mark-briefing-grid__cap">{img.title}</span>}
                  </button>
                );
              })}
            </motion.div>
          </section>
        )}

        {kind === "images" && images.length === 0 && !hero && (
          <p className="mark-briefing-empty">
            Couldn&apos;t load images — check Playwright is installed or try again. Sources
            below may still help.
          </p>
        )}

        <section className="mark-briefing-section">
          <h3 className="mark-briefing-section__title">Summary</h3>
          <p className="mark-briefing-summary">{briefing.summary}</p>
        </section>

        {facts.length > 0 && (
          <section className="mark-briefing-section">
            <h3 className="mark-briefing-section__title">Key points</h3>
            <ul className="mark-briefing-facts">
              {facts.map((f) => (
                <li key={f.slice(0, 48)}>{f}</li>
              ))}
            </ul>
          </section>
        )}

        {sources.length > 0 && (
          <section className="mark-briefing-section">
            <h3 className="mark-briefing-section__title">Sources</h3>
            <ul className="mark-briefing-sources">
              {sources.map((s) => (
                <li key={s.url} className="mark-briefing-source">
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mark-briefing-source__title"
                  >
                    {s.title || host(s.url)}
                  </a>
                  <span className="mark-briefing-source__host">{host(s.url)}</span>
                  {s.snippet && <p className="mark-briefing-source__snippet">{s.snippet}</p>}
                </li>
              ))}
            </ul>
          </section>
        )}
      </motion.div>

      {lightbox && (
        <div
          className="mark-briefing-lightbox"
          role="dialog"
          onClick={() => setLightbox(null)}
          onKeyDown={(e) => e.key === "Escape" && setLightbox(null)}
        >
          <img src={proxiedImageUrl(lightbox, token)} alt="" />
        </div>
      )}
    </motion.div>
  );
}
