import { Canvas, useFrame } from "@react-three/fiber";
import { motion } from "framer-motion";
import { useRef, useMemo } from "react";
import * as THREE from "three";
import type { OrbState } from "@mark/shared";

function OrbMesh({ state, amplitude }: { state: OrbState; amplitude: number }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const materialRef = useRef<THREE.ShaderMaterial>(null);

  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uPulse: { value: 0 },
      uAccent: { value: new THREE.Color("#4a6d94") },
    }),
    []
  );

  const vertexShader = `
    varying vec3 vNormal;
    varying vec3 vPos;
    uniform float uTime;
    uniform float uPulse;
    void main() {
      vNormal = normal;
      vec3 pos = position + normal * sin(uTime * 2.0 + position.y * 4.0) * 0.03 * (1.0 + uPulse);
      vPos = pos;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
    }
  `;

  const fragmentShader = `
    varying vec3 vNormal;
    varying vec3 vPos;
    uniform vec3 uAccent;
    uniform float uTime;
  void main() {
      float fresnel = pow(1.0 - dot(normalize(vNormal), vec3(0.0, 0.0, 1.0)), 2.0);
      vec3 base = vec3(0.04, 0.05, 0.07);
      vec3 col = mix(base, uAccent, fresnel * 0.6 + 0.1);
      float glow = 0.15 + fresnel * 0.5;
      gl_FragColor = vec4(col * glow, 0.95);
    }
  `;

  useFrame((_, delta) => {
    if (!materialRef.current || !meshRef.current) return;
    materialRef.current.uniforms.uTime.value += delta;
    const speed =
      state === "thinking"
        ? 2.5
        : state === "executing"
          ? 3.5
          : state === "listening"
            ? 1.5 + amplitude * 4
            : 0.8;
    materialRef.current.uniforms.uTime.value += delta * speed;
    materialRef.current.uniforms.uPulse.value = THREE.MathUtils.lerp(
      materialRef.current.uniforms.uPulse.value,
      state === "idle" ? 0.2 : 0.6 + amplitude,
      0.08
    );
    meshRef.current.rotation.y += delta * (state === "executing" ? 0.4 : 0.15);
  });

  return (
    <mesh ref={meshRef}>
      <icosahedronGeometry args={[1.2, 64]} />
      <shaderMaterial
        ref={materialRef}
        uniforms={uniforms}
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        transparent
      />
    </mesh>
  );
}

interface MarkOrbProps {
  state: OrbState;
  amplitude?: number;
  className?: string;
}

export function MarkOrb({ state, amplitude = 0, className = "" }: MarkOrbProps) {
  return (
    <motion.div className={`relative w-full max-w-md aspect-square mx-auto ${className}`}>
      <Canvas camera={{ position: [0, 0, 3.5], fov: 45 }} gl={{ alpha: true, antialias: true }}>
        <ambientLight intensity={0.2} />
        <pointLight position={[4, 4, 4]} intensity={0.8} color="#4a6d94" />
        <OrbMesh state={state} amplitude={amplitude} />
      </Canvas>
    </motion.div>
  );
}
