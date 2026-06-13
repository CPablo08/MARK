import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import type { OrbState } from "@mark/shared";

const COUNT = 3200;

function ParticleCloud({ state, amplitude }: { state: OrbState; amplitude: number }) {
  const pointsRef = useRef<THREE.Points>(null);
  const materialRef = useRef<THREE.PointsMaterial>(null);

  const { positions, basePositions } = useMemo(() => {
    const positions = new Float32Array(COUNT * 3);
    const basePositions = new Float32Array(COUNT * 3);
    for (let i = 0; i < COUNT; i++) {
      const phi = Math.acos(1 - (2 * (i + 0.5)) / COUNT);
      const theta = Math.PI * (1 + Math.sqrt(5)) * i;
      const r = 1.15 + (Math.random() - 0.5) * 0.08;
      const x = r * Math.sin(phi) * Math.cos(theta);
      const y = r * Math.sin(phi) * Math.sin(theta);
      const z = r * Math.cos(phi);
      basePositions[i * 3] = x;
      basePositions[i * 3 + 1] = y;
      basePositions[i * 3 + 2] = z;
      positions[i * 3] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;
    }
    return { positions, basePositions };
  }, []);

  useFrame((stateObj) => {
    if (!pointsRef.current || !materialRef.current) return;
    const t = stateObj.clock.elapsedTime;
    const geo = pointsRef.current.geometry as THREE.BufferGeometry;
    const pos = geo.attributes.position as THREE.BufferAttribute;
    const arr = pos.array as Float32Array;

    const pulse =
      state === "listening"
        ? 0.12 + amplitude * 0.35
        : state === "thinking"
          ? 0.08 + Math.sin(t * 3) * 0.04
          : state === "executing"
            ? 0.1 + Math.sin(t * 5) * 0.06
            : 0.04 + Math.sin(t * 0.8) * 0.02;

    const speed = state === "executing" ? 2.2 : state === "thinking" ? 1.6 : 0.9;

    for (let i = 0; i < COUNT; i++) {
      const bx = basePositions[i * 3];
      const by = basePositions[i * 3 + 1];
      const bz = basePositions[i * 3 + 2];
      const n =
        Math.sin(t * speed + bx * 4 + by * 3) * pulse +
        Math.cos(t * 0.7 + bz * 5) * pulse * 0.5;
      const scale = 1 + n;
      arr[i * 3] = bx * scale;
      arr[i * 3 + 1] = by * scale;
      arr[i * 3 + 2] = bz * scale;
    }
    pos.needsUpdate = true;

    pointsRef.current.rotation.y = t * (state === "executing" ? 0.35 : 0.12);
    pointsRef.current.rotation.x = Math.sin(t * 0.2) * 0.12 + amplitude * 0.15;
    pointsRef.current.rotation.z = Math.cos(t * 0.11) * 0.04;

    const accent = state === "listening" ? 0.95 : state === "thinking" ? 0.85 : 0.7;
    materialRef.current.opacity = THREE.MathUtils.lerp(
      materialRef.current.opacity,
      accent + amplitude * 0.2,
      0.06
    );
    materialRef.current.size =
      state === "listening" ? 2.2 + amplitude * 2.5 : state === "executing" ? 2.0 : 1.6;
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial
        ref={materialRef}
        color="#5eead4"
        size={1.8}
        transparent
        opacity={0.75}
        sizeAttenuation
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}

interface ParticleSphereProps {
  state: OrbState;
  amplitude?: number;
  className?: string;
}

export function ParticleSphere({ state, amplitude = 0, className = "" }: ParticleSphereProps) {
  return (
    <div className={`relative w-full h-full min-h-[280px] ${className}`}>
      <div
        className="absolute inset-0 pointer-events-none rounded-full opacity-40"
        style={{
          background:
            "radial-gradient(circle at 50% 45%, rgba(45,212,191,0.15) 0%, transparent 55%)",
        }}
      />
      <Canvas camera={{ position: [0, 0, 3.2], fov: 50 }} gl={{ alpha: true, antialias: true }}>
        <ambientLight intensity={0.15} />
        <pointLight position={[3, 2, 4]} intensity={1.2} color="#2dd4bf" />
        <pointLight position={[-3, -2, 2]} intensity={0.4} color="#4a6d94" />
        <ParticleCloud state={state} amplitude={amplitude} />
      </Canvas>
    </div>
  );
}
