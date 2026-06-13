import { useEffect, useRef } from "react";

/** Full-viewport background dot grid (reference-style). */
export function DotGridBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let raf = 0;
    let running = true;

    const draw = (t: number) => {
      if (!running) return;
      const parent = canvas.parentElement;
      if (!parent) return;

      const w = parent.clientWidth;
      const h = parent.clientHeight;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      ctx.clearRect(0, 0, w, h);

      const spacing = 22;
      const pulse = 0.85 + Math.sin(t * 0.0008) * 0.15;

      for (let x = spacing / 2; x < w; x += spacing) {
        for (let y = spacing / 2; y < h; y += spacing) {
          const dx = x - w / 2;
          const dy = y - h / 2;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const falloff = Math.max(0.2, 1 - dist / (Math.max(w, h) * 0.72));
          const twinkle =
            0.7 +
            0.3 * Math.sin(t * 0.0012 + x * 0.02 + y * 0.015);
          const alpha = Math.min(0.95, 0.62 * falloff * twinkle * pulse);
          const radius = 0.9 + falloff * 0.6;

          const g = ctx.createRadialGradient(x, y, 0, x, y, radius * 2.5);
          g.addColorStop(0, `rgba(90, 125, 175, ${alpha})`);
          g.addColorStop(0.5, `rgba(65, 95, 140, ${alpha * 0.5})`);
          g.addColorStop(1, "rgba(40, 58, 85, 0)");
          ctx.fillStyle = g;
          ctx.beginPath();
          ctx.arc(x, y, radius, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      raf = requestAnimationFrame(draw);
    };

    raf = requestAnimationFrame(draw);
    const ro = new ResizeObserver(() => {});
    if (canvas.parentElement) ro.observe(canvas.parentElement);

    return () => {
      running = false;
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, []);

  return <canvas ref={canvasRef} className="mark-dot-grid-canvas" aria-hidden />;
}
