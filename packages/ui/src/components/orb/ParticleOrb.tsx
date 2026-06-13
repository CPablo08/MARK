import { useEffect, useMemo, useRef } from "react";
import type { OrbState } from "@mark/shared";

const COUNT = 2800;

interface Particle {
  bx: number;
  by: number;
  bz: number;
}

function fibonacciSphere(n: number): Particle[] {
  const pts: Particle[] = [];
  const golden = Math.PI * (3 - Math.sqrt(5));
  for (let i = 0; i < n; i++) {
    const y = 1 - (i / (n - 1)) * 2;
    const r = Math.sqrt(1 - y * y);
    const theta = golden * i;
    const jitter = 0.96 + Math.random() * 0.08;
    pts.push({
      bx: Math.cos(theta) * r * jitter,
      by: y * jitter,
      bz: Math.sin(theta) * r * jitter,
    });
  }
  return pts;
}

function rotateY(p: Particle, a: number) {
  const c = Math.cos(a);
  const s = Math.sin(a);
  return { x: p.bx * c + p.bz * s, y: p.by, z: -p.bx * s + p.bz * c };
}

function rotateX(p: { x: number; y: number; z: number }, a: number) {
  const c = Math.cos(a);
  const s = Math.sin(a);
  return { x: p.x, y: p.y * c - p.z * s, z: p.y * s + p.z * c };
}

interface ParticleOrbProps {
  state: OrbState;
  amplitude?: number;
  onHover?: (hovering: boolean) => void;
  /** Smaller render for corner voice dock */
  compact?: boolean;
}

export function ParticleOrb({
  state,
  amplitude = 0,
  onHover,
  compact = false,
}: ParticleOrbProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const count = compact ? 1400 : COUNT;
  const particles = useMemo(() => fibonacciSphere(count), [count]);
  const mouseRef = useRef({ x: 0, y: 0, active: false });
  const rotRef = useRef({ x: 0.15, y: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    let raf = 0;
    let running = true;
    let logicalSize = 400;

    const resize = () => {
      const parent = canvas.parentElement;
      if (!parent) return;
      const cap = compact ? 96 : 480;
      logicalSize = Math.min(parent.clientWidth, parent.clientHeight, cap) || (compact ? 88 : 400);
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = logicalSize * dpr;
      canvas.height = logicalSize * dpr;
      canvas.style.width = `${logicalSize}px`;
      canvas.style.height = `${logicalSize}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const ro = new ResizeObserver(resize);
    ro.observe(canvas.parentElement ?? canvas);
    resize();

    const tick = (now: number) => {
      if (!running) return;
      const t = now * 0.001;
      const w = logicalSize;
      const h = logicalSize;
      const cx = w / 2;
      const cy = h / 2;
      const scale = Math.min(w, h) * 0.38;

      const speed =
        state === "executing" ? 0.55 : state === "thinking" ? 0.38 : state === "listening" ? 0.28 : 0.18;
      rotRef.current.y += speed * 0.012;
      rotRef.current.x = 0.12 + Math.sin(t * 0.35) * 0.06 + amplitude * 0.25;

      if (mouseRef.current.active) {
        rotRef.current.y += mouseRef.current.x * 0.0004;
        rotRef.current.x += mouseRef.current.y * 0.0003;
      }

      const pulse =
        state === "listening"
          ? 0.06 + amplitude * 0.14
          : state === "thinking"
            ? 0.04 + Math.sin(t * 4) * 0.025
            : state === "executing"
              ? 0.05 + Math.sin(t * 6) * 0.035
              : 0.02 + Math.sin(t * 0.9) * 0.015;

      ctx.clearRect(0, 0, w, h);

      const projected: { x: number; y: number; z: number; i: number }[] = [];

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        const wave =
          Math.sin(t * 2.2 + p.bx * 5 + p.by * 4) * pulse +
          Math.cos(t * 1.1 + p.bz * 6) * pulse * 0.5;
        const inflated = { bx: p.bx * (1 + wave), by: p.by * (1 + wave), bz: p.bz * (1 + wave) };
        let r = rotateY(inflated, rotRef.current.y);
        r = rotateX(r, rotRef.current.x);
        projected.push({
          x: cx + r.x * scale,
          y: cy + r.y * scale,
          z: r.z,
          i,
        });
      }

      projected.sort((a, b) => a.z - b.z);

      for (const p of projected) {
        const depth = (p.z + 1) * 0.5;
        const alpha = 0.15 + depth * 0.75;
        const radius = 0.45 + depth * 1.15 + (state === "listening" ? amplitude * 1.2 : 0);
        const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, radius * 2);
        const core =
          state === "listening"
            ? `rgba(110, 145, 195, ${alpha})`
            : state === "executing"
              ? `rgba(85, 120, 175, ${alpha})`
              : `rgba(75, 108, 155, ${alpha * 0.95})`;
        g.addColorStop(0, core);
        g.addColorStop(1, "rgba(45, 65, 95, 0)");
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
        ctx.fill();
      }

      raf = requestAnimationFrame(tick);
    };

    raf = requestAnimationFrame(tick);
    return () => {
      running = false;
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, [particles, state, amplitude]);

  return (
    <canvas
      ref={canvasRef}
      className="mark-particle-orb"
      aria-label="MARK particle sphere"
      onMouseEnter={() => onHover?.(true)}
      onMouseLeave={() => {
        mouseRef.current.active = false;
        onHover?.(false);
      }}
      onMouseMove={(e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        mouseRef.current = {
          x: (e.clientX - rect.left) / rect.width - 0.5,
          y: (e.clientY - rect.top) / rect.height - 0.5,
          active: true,
        };
      }}
    />
  );
}
