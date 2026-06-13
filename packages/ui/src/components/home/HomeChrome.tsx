import { useEffect, useState } from "react";
import { useMarkStore } from "../../store/markStore";

export function HomeClock() {
  const [time, setTime] = useState(() => new Date().toLocaleTimeString());

  useEffect(() => {
    const id = setInterval(() => setTime(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(id);
  }, []);

  return <div className="mark-clock">{time}</div>;
}

export function HomeZoomControls() {
  const zoom = useMarkStore((s) => s.orbZoom);
  const setOrbZoom = useMarkStore((s) => s.setOrbZoom);

  return (
    <div className="mark-float-panel mark-zoom-bar">
      <span className="text-[10px] text-muted tabular-nums w-9 text-center">
        {Math.round(zoom * 100)}%
      </span>
      <button type="button" className="mark-icon-btn" onClick={() => setOrbZoom(zoom + 0.1)} aria-label="Zoom in">
        +
      </button>
      <button type="button" className="mark-icon-btn" onClick={() => setOrbZoom(zoom - 0.1)} aria-label="Zoom out">
        −
      </button>
      <button type="button" className="mark-icon-btn" onClick={() => setOrbZoom(1)} aria-label="Reset zoom">
        ⊡
      </button>
    </div>
  );
}
