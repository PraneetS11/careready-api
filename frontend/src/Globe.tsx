import { Component, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { BufferGeometry, Float32BufferAttribute, Vector3 } from "three";
import { useReducedMotion } from "motion/react";
import { Pause, Play, RotateCcw } from "lucide-react";
import type { Visit } from "./types";
function point(lat: number, lon: number, r = 2) {
  const phi = (lat * Math.PI) / 180;
  const theta = (lon * Math.PI) / 180;
  return new Vector3(
    r * Math.cos(phi) * Math.sin(theta),
    r * Math.sin(phi),
    r * Math.cos(phi) * Math.cos(theta),
  );
}
type Land = {
  features: {
    geometry: { type: string; coordinates: number[][][] | number[][][][] };
  }[];
};
function Earth({
  jobs,
  onSelect,
}: {
  jobs: Visit[];
  onSelect: (v: Visit) => void;
}) {
  const [land, setLand] = useState<Land>();
  useEffect(() => {
    const controller = new AbortController();
    fetch("/land.json", { signal: controller.signal })
      .then((r) => r.json())
      .then(setLand)
      .catch(() => {});
    return () => controller.abort();
  }, []);
  const coast = useMemo(() => {
    const positions: number[] = [];
    land?.features.forEach((f) => {
      const polygons =
        f.geometry.type === "Polygon"
          ? [f.geometry.coordinates as number[][][]]
          : (f.geometry.coordinates as number[][][][]);
      polygons.forEach((poly) =>
        poly.forEach((ring) => {
          for (let i = 1; i < ring.length; i++) {
            positions.push(
              ...point(ring[i - 1][1], ring[i - 1][0], 2.006).toArray(),
              ...point(ring[i][1], ring[i][0], 2.006).toArray(),
            );
          }
        }),
      );
    });
    const g = new BufferGeometry();
    g.setAttribute("position", new Float32BufferAttribute(positions, 3));
    return g;
  }, [land]);
  useEffect(() => () => coast.dispose(), [coast]);
  const cities = [...new Map(jobs.map((j) => [j.city, j])).values()];
  return (
    <group rotation={[0.13, 1.05, 0]}>
      <mesh>
        <sphereGeometry args={[2, 64, 64]} />
        <meshStandardMaterial color="#1f5145" roughness={0.85} />
      </mesh>
      <mesh>
        <sphereGeometry args={[2.012, 24, 16]} />
        <meshBasicMaterial
          color="#77a995"
          wireframe
          transparent
          opacity={0.08}
        />
      </mesh>
      <lineSegments geometry={coast}>
        <lineBasicMaterial color="#b0c5a2" transparent opacity={0.65} />
      </lineSegments>
      {cities.map((j) => (
        <group key={j.city} position={point(j.latitude, j.longitude, 2.04)}>
          <mesh
            onClick={(e) => {
              e.stopPropagation();
              onSelect(j);
            }}
            onPointerOver={() => {
              document.body.style.cursor = "pointer";
            }}
            onPointerOut={() => {
              document.body.style.cursor = "auto";
            }}
          >
            <sphereGeometry args={[0.055, 16, 16]} />
            <meshBasicMaterial color="#ffc181" />
          </mesh>
          <mesh>
            <sphereGeometry args={[0.085, 16, 16]} />
            <meshBasicMaterial color="#ffc181" transparent opacity={0.17} />
          </mesh>
        </group>
      ))}
    </group>
  );
}
class MapBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? (
      <div className="map-fallback">
        The globe is unavailable on this device.
        <br />
        All available visits are listed below.
      </div>
    ) : (
      this.props.children
    );
  }
}
export default function Globe({
  jobs,
  onSelect,
}: {
  jobs: Visit[];
  onSelect: (v: Visit) => void;
}) {
  const reduced = useReducedMotion();
  const [spinning, setSpinning] = useState(!reduced);
  const [key, setKey] = useState(0);
  return (
    <div className="globe-wrap">
      <div className="globe-halo" />
      <MapBoundary>
        <Canvas
          key={key}
          camera={{ position: [0, 0.1, 5.8], fov: 45 }}
          dpr={[1, 1.5]}
          aria-label="Interactive globe showing approximate cities for available visits"
        >
          <ambientLight intensity={1.6} />
          <directionalLight position={[-3, 4, 5]} intensity={2} />
          <Earth jobs={jobs} onSelect={onSelect} />
          <OrbitControls
            enablePan={false}
            minDistance={4.5}
            maxDistance={8}
            autoRotate={spinning && !reduced}
            autoRotateSpeed={0.35}
          />
        </Canvas>
      </MapBoundary>
      <div className="globe-controls">
        <button
          aria-label={
            spinning ? "Pause globe rotation" : "Start globe rotation"
          }
          onClick={() => setSpinning(!spinning)}
        >
          {spinning ? <Pause size={14} /> : <Play size={14} />}
        </button>
        <button aria-label="Reset globe view" onClick={() => setKey(key + 1)}>
          <RotateCcw size={14} />
        </button>
        <span>Drag to explore · Scroll to zoom</span>
      </div>
    </div>
  );
}
