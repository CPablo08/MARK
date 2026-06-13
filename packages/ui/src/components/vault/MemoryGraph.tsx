import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { useMarkStore } from "../../store/markStore";

interface GraphNode {
  id: string;
  label: string;
  category: string;
  color: string;
  size: number;
  content: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

interface GraphLink {
  source: string;
  target: string;
}

const CATEGORIES = [
  { id: "credential", label: "Credentials", color: "#9a7a6a" },
  { id: "semantic", label: "Semantic", color: "#4a6d94" },
  { id: "episodic", label: "Episodic", color: "#6a7a9a" },
  { id: "procedural", label: "Procedural", color: "#5a7a9a" },
  { id: "project", label: "Projects", color: "#7a8aa8" },
  { id: "agent", label: "Agents", color: "#4a6d94" },
];

export function MemoryGraph() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const token = useMarkStore((s) => s.token);
  const selectedId = useMarkStore((s) => s.selectedMemoryId);
  const setSelectedId = useMarkStore((s) => s.setSelectedMemoryId);
  const nodesRef = useRef<GraphNode[]>([]);
  const linksRef = useRef<GraphLink[]>([]);
  const [hovered, setHovered] = useState<GraphNode | null>(null);
  const [foldersOpen, setFoldersOpen] = useState(false);

  const { data } = useQuery({
    queryKey: ["memory-graph", token],
    queryFn: () => api.memoryGraph(token!),
    enabled: !!token,
  });

  useEffect(() => {
    if (!data) return;
    const w = 800;
    const h = 600;
    nodesRef.current = data.nodes.map((n, i) => ({
      ...n,
      x: w / 2 + Math.cos((i / data.nodes.length) * Math.PI * 2) * 180,
      y: h / 2 + Math.sin((i / data.nodes.length) * Math.PI * 2) * 180,
      vx: 0,
      vy: 0,
    }));
    linksRef.current = data.links;
  }, [data]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let anim = 0;
    const nodeMap = () => new Map(nodesRef.current.map((n) => [n.id, n]));

    const tick = () => {
      const rect = canvas.getBoundingClientRect();
      const w = rect.width;
      const h = rect.height;
      if (canvas.width !== w) canvas.width = w;
      if (canvas.height !== h) canvas.height = h;

      const nodes = nodesRef.current;
      const links = linksRef.current;
      const map = nodeMap();

      for (const n of nodes) {
        n.vx = (n.vx ?? 0) + (w / 2 - (n.x ?? 0)) * 0.0008;
        n.vy = (n.vy ?? 0) + (h / 2 - (n.y ?? 0)) * 0.0008;
      }
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = (nodes[j].x ?? 0) - (nodes[i].x ?? 0);
          const dy = (nodes[j].y ?? 0) - (nodes[i].y ?? 0);
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const rep = 1200 / (dist * dist);
          nodes[i].vx = (nodes[i].vx ?? 0) - (dx / dist) * rep;
          nodes[i].vy = (nodes[i].vy ?? 0) - (dy / dist) * rep;
          nodes[j].vx = (nodes[j].vx ?? 0) + (dx / dist) * rep;
          nodes[j].vy = (nodes[j].vy ?? 0) + (dy / dist) * rep;
        }
      }
      for (const l of links) {
        const a = map.get(l.source);
        const b = map.get(l.target);
        if (!a || !b) continue;
        const dx = (b.x ?? 0) - (a.x ?? 0);
        const dy = (b.y ?? 0) - (a.y ?? 0);
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const pull = (dist - 90) * 0.002;
        a.vx = (a.vx ?? 0) + (dx / dist) * pull;
        a.vy = (a.vy ?? 0) + (dy / dist) * pull;
        b.vx = (b.vx ?? 0) - (dx / dist) * pull;
        b.vy = (b.vy ?? 0) - (dy / dist) * pull;
      }

      for (const n of nodes) {
        n.vx = (n.vx ?? 0) * 0.88;
        n.vy = (n.vy ?? 0) * 0.88;
        n.x = (n.x ?? 0) + (n.vx ?? 0);
        n.y = (n.y ?? 0) + (n.vy ?? 0);
        n.x = Math.max(40, Math.min(w - 40, n.x ?? 0));
        n.y = Math.max(40, Math.min(h - 40, n.y ?? 0));
      }

      ctx.fillStyle = "#050607";
      ctx.fillRect(0, 0, w, h);

      ctx.fillStyle = "rgba(148,163,184,0.08)";
      for (let x = 0; x < w; x += 24) {
        for (let y = 0; y < h; y += 24) {
          ctx.beginPath();
          ctx.arc(x, y, 0.8, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      for (const l of links) {
        const a = map.get(l.source);
        const b = map.get(l.target);
        if (!a || !b) continue;
        ctx.strokeStyle = "rgba(148,163,184,0.12)";
        ctx.lineWidth = 0.6;
        ctx.beginPath();
        ctx.moveTo(a.x ?? 0, a.y ?? 0);
        ctx.lineTo(b.x ?? 0, b.y ?? 0);
        ctx.stroke();
      }

      for (const n of nodes) {
        const r = n.size + (selectedId === n.id ? 3 : 0);
        const glow = selectedId === n.id || hovered?.id === n.id;
        if (glow) {
          ctx.shadowColor = n.color;
          ctx.shadowBlur = 12;
        }
        ctx.fillStyle = n.color;
        ctx.globalAlpha = n.id === "mark-core" ? 1 : 0.85;
        ctx.beginPath();
        ctx.arc(n.x ?? 0, n.y ?? 0, r, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
        ctx.globalAlpha = 1;
      }

      anim = requestAnimationFrame(tick);
    };
    anim = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(anim);
  }, [data, selectedId, hovered]);

  const pickNode = (x: number, y: number, radius: number) => {
    let best: GraphNode | null = null;
    let bestD = radius;
    for (const n of nodesRef.current) {
      const d = Math.hypot((n.x ?? 0) - x, (n.y ?? 0) - y);
      if (d < bestD) {
        bestD = d;
        best = n;
      }
    }
    return best;
  };

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const best = pickNode(e.clientX - rect.left, e.clientY - rect.top, 20);
    setSelectedId(best?.id === "mark-core" ? null : best?.id ?? null);
    setHovered(best);
  };

  const handleMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    setHovered(pickNode(e.clientX - rect.left, e.clientY - rect.top, 16));
  };

  const detail =
    hovered ?? data?.nodes.find((n) => n.id === selectedId) ?? null;

  return (
    <div className="flex h-full min-h-0">
      <aside
        className={`shrink-0 border-r border-border/60 bg-graphite/90 flex flex-col ${
          foldersOpen ? "w-48" : "w-9"
        }`}
      >
        <button
          type="button"
          onClick={() => setFoldersOpen((v) => !v)}
          className="px-2 py-3 border-b border-border/40 text-muted hover:text-gray-200 text-xs w-full"
          aria-expanded={foldersOpen}
        >
          {foldersOpen ? "▾" : "▸"}
        </button>
        {foldersOpen && (
        <nav className="flex-1 overflow-y-auto py-2 text-[11px]">
          {CATEGORIES.map((c) => {
            const count = data?.nodes.filter((n) => n.category === c.id).length ?? 0;
            return (
              <motion.div
                key={c.id}
                className="flex items-center gap-2 px-3 py-1.5 text-gray-500 hover:text-gray-200"
                whileHover={{ x: 2 }}
              >
                <span className="w-2 h-2 rounded-full shrink-0" style={{ background: c.color }} />
                <span className="flex-1 truncate">{c.label}</span>
                <span className="text-[9px] tabular-nums text-gray-600">{count}</span>
              </motion.div>
            );
          })}
        </nav>
        )}
      </aside>
      <motion.div className="flex flex-col flex-1 min-w-0 min-h-0" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <div className="flex items-center justify-between px-4 py-3 border-b border-border/60 shrink-0">
          <div>
            <h2 className="text-sm font-medium text-white tracking-tight">Memory map</h2>
            <p className="text-[10px] text-muted uppercase tracking-widest mt-0.5">
              {data?.nodes.length ?? 0} nodes · {data?.links.length ?? 0} links
            </p>
          </div>
        </div>
        <div className="flex-1 relative min-h-0">
          <canvas
            ref={canvasRef}
            className="w-full h-full cursor-crosshair"
            onClick={handleClick}
            onMouseMove={handleMove}
            onMouseLeave={() => setHovered(null)}
          />
          {detail && detail.id !== "mark-core" && (
            <div className="absolute bottom-4 left-4 max-w-md p-3 rounded-lg bg-graphite/95 border border-border/80 backdrop-blur text-xs">
              <span className="text-accent uppercase tracking-wider text-[9px]">{detail.category}</span>
              <p className="text-gray-300 mt-1 leading-relaxed">{detail.content}</p>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
