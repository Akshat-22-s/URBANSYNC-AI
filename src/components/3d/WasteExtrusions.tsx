'use client';

import React, { useMemo, useRef, useState } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import { useUrbanSyncStore } from '@/store/useUrbanSyncStore';
import type { WasteNode } from '@/types';
import { SAMPLE_WASTE_NODES, geoToScene } from './sceneConfig';

const MAX_HEIGHT = 3.0;

function getFillColor(fillPct: number): string {
  if (fillPct < 50) return '#10B981'; // Emerald safe
  if (fillPct <= 75) return '#F59E0B'; // Amber warning
  return '#F43F5E'; // Crimson danger / critical
}

interface SingleBinProps {
  bin: WasteNode;
  index: number;
}

const SingleWasteBin: React.FC<SingleBinProps> = React.memo(({ bin, index }) => {
  const [hovered, setHovered] = useState(false);
  const materialRef = useRef<THREE.MeshStandardMaterial>(null);
  const sphereMaterialRef = useRef<THREE.MeshStandardMaterial>(null);

  // Map lat/lon to scene coordinates
  const [sceneX, , sceneZ] = useMemo(() => {
    return geoToScene(bin.lat, bin.lon, 0);
  }, [bin.lat, bin.lon]);

  // Height proportional to fill_pct (clamped between 0.3 and MAX_HEIGHT)
  const height = useMemo(() => {
    const rawHeight = (bin.fill_pct / 100) * MAX_HEIGHT;
    return Math.max(0.35, Math.min(MAX_HEIGHT, rawHeight));
  }, [bin.fill_pct]);

  const baseColor = useMemo(() => getFillColor(bin.fill_pct), [bin.fill_pct]);
  const isCritical = bin.fill_pct > 75;

  // Cylinder geometry for the fill extrusion
  const cylinderGeometry = useMemo(() => {
    return new THREE.CylinderGeometry(0.3, 0.3, height, 8);
  }, [height]);

  // Cylinder geometry for base metallic rim
  const rimGeometry = useMemo(() => {
    return new THREE.CylinderGeometry(0.42, 0.44, 0.1, 12);
  }, []);

  // Top interaction sphere geometry
  const sphereGeometry = useMemo(() => {
    return new THREE.SphereGeometry(0.18, 16, 16);
  }, []);

  // Pulse glow animation for critical overflow (>75%)
  useFrame(({ clock }) => {
    if (isCritical && materialRef.current && sphereMaterialRef.current) {
      const elapsed = clock.getElapsedTime();
      // Oscillate emissive intensity between 0.2 and 0.8
      const intensity = 0.5 + 0.3 * Math.sin(elapsed * 5 + index * 0.7);
      materialRef.current.emissiveIntensity = intensity;
      sphereMaterialRef.current.emissiveIntensity = intensity + 0.2;
    }
  });

  return (
    <group position={[sceneX, 0, sceneZ]}>
      {/* Ground Foundation Rim */}
      <mesh geometry={rimGeometry} position={[0, 0.05, 0]}>
        <meshStandardMaterial color="#0A0F1A" metalness={0.9} roughness={0.3} />
      </mesh>

      {/* Primary Fill Cylinder Extrusion */}
      <mesh
        geometry={cylinderGeometry}
        position={[0, height / 2 + 0.1, 0]}
        onPointerOver={(e) => {
          e.stopPropagation();
          setHovered(true);
        }}
        onPointerOut={() => setHovered(false)}
      >
        <meshStandardMaterial
          ref={materialRef}
          color={baseColor}
          emissive={baseColor}
          emissiveIntensity={isCritical ? 0.5 : 0.15}
          roughness={0.3}
          metalness={0.2}
          transparent
          opacity={0.92}
        />
      </mesh>

      {/* Top Sphere for Raycasting / Pointer Interaction */}
      <mesh
        geometry={sphereGeometry}
        position={[0, height + 0.22, 0]}
        onPointerOver={(e) => {
          e.stopPropagation();
          setHovered(true);
        }}
        onPointerOut={() => setHovered(false)}
      >
        <meshStandardMaterial
          ref={sphereMaterialRef}
          color={baseColor}
          emissive={baseColor}
          emissiveIntensity={isCritical ? 0.7 : 0.3}
          roughness={0.2}
          metalness={0.7}
        />
      </mesh>

      {/* Outer Protective Cage Ring */}
      <mesh position={[0, height + 0.09, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.32, 0.36, 16]} />
        <meshBasicMaterial color="#06B6D4" transparent opacity={0.4} side={THREE.DoubleSide} />
      </mesh>

      {/* Billboard Tag Label Showing Fill Percentage and Node ID */}
      <Html
        position={[0, height + 0.65, 0]}
        center
        distanceFactor={16}
        style={{ pointerEvents: 'none', userSelect: 'none' }}
      >
        <div className="flex flex-col items-center pointer-events-none select-none">
          <span
            className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded shadow-md border"
            style={{
              color: baseColor,
              backgroundColor: 'rgba(6,9,19,0.85)',
              borderColor: `${baseColor}60`,
            }}
          >
            {Math.round(bin.fill_pct)}%
          </span>
          <span className="text-[8px] font-mono text-slate-400 mt-0.5 bg-black/60 px-1 rounded">
            {bin.id}
          </span>
        </div>
      </Html>

      {/* Interactive Cyberpunk Tooltip HUD on Pointer Hover */}
      {hovered && (
        <Html
          position={[0, height + 1.45, 0]}
          center
          distanceFactor={14}
          style={{ pointerEvents: 'none' }}
        >
          <div className="bg-[#060913]/95 border border-[#06B6D4]/60 rounded-md p-3 text-xs font-mono text-slate-200 shadow-[0_0_20px_rgba(6,182,212,0.4)] backdrop-blur-md min-w-[190px] select-none">
            <div className="flex items-center justify-between border-b border-[#06B6D4]/30 pb-1.5 mb-2 font-bold text-white tracking-wider">
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: baseColor }} />
                <span>BIN {bin.id}</span>
              </span>
              <span style={{ color: baseColor }}>{bin.fill_pct}%</span>
            </div>

            <div className="space-y-1 text-[11px] text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-400">Capacity:</span>
                <span className="font-semibold text-white">{bin.capacity_kg} kg</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Demand:</span>
                <span className="font-semibold text-white">
                  {bin.demand_kg !== undefined
                    ? `${bin.demand_kg.toFixed(1)} kg`
                    : `${((bin.capacity_kg * bin.fill_pct) / 100).toFixed(1)} kg`}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Last Collected:</span>
                <span className="text-cyan-300">{bin.last_collected || '14:20 IST'}</span>
              </div>
              <div className="flex justify-between pt-1 border-t border-slate-700/60">
                <span className="text-slate-400">Telemetry Status:</span>
                <span className="font-bold" style={{ color: baseColor }}>
                  {bin.fill_pct > 75
                    ? 'CRITICAL OVERFLOW'
                    : bin.fill_pct >= 50
                    ? 'CAPACITY WARNING'
                    : 'NOMINAL'}
                </span>
              </div>
            </div>
          </div>
        </Html>
      )}
    </group>
  );
});

SingleWasteBin.displayName = 'SingleWasteBin';

export const WasteExtrusions: React.FC = () => {
  const storeWasteBins = useUrbanSyncStore((s) => s.wasteBins);

  // Use store data if present; otherwise fall back to comprehensive sample bins
  const binsToRender = useMemo<WasteNode[]>(() => {
    const list = Object.values(storeWasteBins);
    return list.length > 0 ? list : SAMPLE_WASTE_NODES;
  }, [storeWasteBins]);

  return (
    <group name="waste-extrusions">
      {binsToRender.map((bin, idx) => (
        <SingleWasteBin key={bin.id} bin={bin} index={idx} />
      ))}
    </group>
  );
};

export default React.memo(WasteExtrusions);
