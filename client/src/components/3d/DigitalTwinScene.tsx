'use client';

import React, { useMemo, useEffect, useState, useRef } from 'react';
import dynamic from 'next/dynamic';
import * as THREE from 'three';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Html } from '@react-three/drei';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import { useUrbanSyncStore } from '@/store/useUrbanSyncStore';
import { CITY_BUILDINGS, type BuildingData } from './sceneConfig';
import VolumetricCones from './VolumetricCones';
import WasteExtrusions from './WasteExtrusions';
import EmergencyCorridors from './EmergencyCorridors';
import { LucknowCivicLogo, UrbanSyncLogo } from '../ui/Logos';

// Enhanced Building with Glass Facades and Glowing Windows
const BuildingBlock: React.FC<{ building: BuildingData; index: number }> = React.memo(({ building, index }) => {
  const geom = useMemo(
    () => new THREE.BoxGeometry(building.w, building.h, building.d),
    [building.w, building.h, building.d]
  );

  const edgesGeom = useMemo(() => new THREE.EdgesGeometry(geom), [geom]);
  const isTall = building.h >= 6.0;
  const isCommercial = building.w >= 5.0 && building.d >= 5.0;

  // Varied building themes based on index for architectural realism
  const buildingColor = isCommercial ? '#1e293b' : index % 3 === 0 ? '#334155' : '#243044';

  return (
    <group position={[building.x, building.h / 2, building.z]}>
      {/* Structural Building Body */}
      <mesh geometry={geom} castShadow receiveShadow>
        <meshStandardMaterial
          color={buildingColor}
          roughness={0.25}
          metalness={0.6}
        />
      </mesh>

      {/* Cyber Edge Wireframes */}
      <lineSegments geometry={edgesGeom}>
        <lineBasicMaterial color="#38BDF8" transparent opacity={0.45} />
      </lineSegments>

      {/* Illuminated Window Bands on Facades */}
      {isTall && (
        <group position={[0, 0, building.d / 2 + 0.01]}>
          <mesh position={[0, building.h * 0.2, 0]}>
            <planeGeometry args={[building.w * 0.8, 0.2]} />
            <meshBasicMaterial color="#38BDF8" transparent opacity={0.6} side={THREE.DoubleSide} />
          </mesh>
          <mesh position={[0, 0, 0]}>
            <planeGeometry args={[building.w * 0.8, 0.2]} />
            <meshBasicMaterial color="#06B6D4" transparent opacity={0.6} side={THREE.DoubleSide} />
          </mesh>
          <mesh position={[0, -building.h * 0.2, 0]}>
            <planeGeometry args={[building.w * 0.8, 0.2]} />
            <meshBasicMaterial color="#38BDF8" transparent opacity={0.6} side={THREE.DoubleSide} />
          </mesh>
        </group>
      )}

      {/* Rooftop Tactical Antenna Beacon */}
      {isTall && (
        <group position={[0, building.h / 2 + 0.45, 0]}>
          <mesh>
            <cylinderGeometry args={[0.04, 0.04, 0.9, 6]} />
            <meshStandardMaterial color="#94A3B8" metalness={0.9} />
          </mesh>
          <mesh position={[0, 0.48, 0]}>
            <sphereGeometry args={[0.12, 12, 12]} />
            <meshStandardMaterial color="#06B6D4" emissive="#06B6D4" emissiveIntensity={1.2} />
          </mesh>
        </group>
      )}

      {/* Rooftop Helipad / Solar Array for Commercial Blocks */}
      {isCommercial && (
        <mesh position={[0, building.h / 2 + 0.02, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[1.4, 1.65, 24]} />
          <meshBasicMaterial color="#10B981" transparent opacity={0.4} side={THREE.DoubleSide} />
        </mesh>
      )}
    </group>
  );
});

BuildingBlock.displayName = 'BuildingBlock';

// Floating 3D City Landmarks with Badges
const CityLandmarks: React.FC = () => {
  return (
    <group>
      {/* Landmark 1: Lucknow Municipal Command HQ */}
      <group position={[0, 8.5, 0]}>
        <Html center distanceFactor={22} style={{ pointerEvents: 'none', userSelect: 'none' }}>
          <div className="flex items-center gap-1.5 bg-[#0f172a]/95 border border-cyan-400/80 px-2.5 py-1 rounded-md shadow-[0_0_15px_rgba(6,182,212,0.5)] backdrop-blur-md whitespace-nowrap">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            <span className="text-[10px] font-mono font-bold text-cyan-300 tracking-wider">LUCKNOW CIVIC HQ</span>
          </div>
        </Html>
      </group>

      {/* Landmark 2: Hazratganj Smart Corridor */}
      <group position={[-16, 7.5, -4]}>
        <Html center distanceFactor={22} style={{ pointerEvents: 'none', userSelect: 'none' }}>
          <div className="flex items-center gap-1.5 bg-[#0f172a]/95 border border-emerald-400/80 px-2.5 py-1 rounded-md shadow-[0_0_15px_rgba(16,185,129,0.4)] backdrop-blur-md whitespace-nowrap">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span className="text-[10px] font-mono font-bold text-emerald-300 tracking-wider">HAZRATGANJ GREEN WAVE</span>
          </div>
        </Html>
      </group>

      {/* Landmark 3: Pink Booth Safe Haven #4 */}
      <group position={[12, 6.5, 8]}>
        <Html center distanceFactor={22} style={{ pointerEvents: 'none', userSelect: 'none' }}>
          <div className="flex items-center gap-1.5 bg-[#0f172a]/95 border border-pink-500/80 px-2.5 py-1 rounded-md shadow-[0_0_15px_rgba(236,72,153,0.4)] backdrop-blur-md whitespace-nowrap">
            <span className="w-2 h-2 rounded-full bg-pink-400 animate-pulse" />
            <span className="text-[10px] font-mono font-bold text-pink-300 tracking-wider">PINK BOOTH #4 [SAFE ZONE]</span>
          </div>
        </Html>
      </group>
    </group>
  );
};

// Illuminated Smart City Environment: Daylight Atmosphere, Roads, Water, Parks
const SceneEnvironment: React.FC = React.memo(() => {
  const gridHelper = useMemo(() => {
    const grid = new THREE.GridHelper(60, 60, 0x0284c7, 0x334155);
    (grid.material as THREE.Material).transparent = true;
    (grid.material as THREE.Material).opacity = 0.28;
    return grid;
  }, []);

  return (
    <>
      {/* Lightened Twilight Atmosphere Fog */}
      <fog attach="fog" args={['#0f172a', 32, 95]} />

      {/* Balanced Hemisphere Ambient Light (Sky Blue + Slate Bounce) */}
      <hemisphereLight
        args={['#38bdf8', '#0f172a', 0.9]}
      />

      {/* Soft Omnidirectional Ambient Light */}
      <ambientLight intensity={0.65} color="#e2e8f0" />

      {/* Primary Directional Sunlight with Shadows */}
      <directionalLight
        position={[25, 45, 20]}
        intensity={2.2}
        color="#ffffff"
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-near={10}
        shadow-camera-far={100}
        shadow-camera-left={-30}
        shadow-camera-right={30}
        shadow-camera-top={30}
        shadow-camera-bottom={-30}
      />

      {/* Secondary Cyan Rim Fill Light */}
      <directionalLight
        position={[-25, 25, -20]}
        intensity={0.7}
        color="#06B6D4"
      />

      {/* Luminous Ground Plane: Slate Blue Foundation */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]} receiveShadow>
        <planeGeometry args={[120, 120]} />
        <meshStandardMaterial
          color="#0f172a"
          roughness={0.7}
          metalness={0.2}
        />
      </mesh>

      {/* Main East-West Illuminated Highway Arterial */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]}>
        <planeGeometry args={[60, 3.5]} />
        <meshStandardMaterial color="#1e293b" roughness={0.8} />
      </mesh>

      {/* Highway Glowing Centerline */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.005, 0]}>
        <planeGeometry args={[60, 0.12]} />
        <meshBasicMaterial color="#38BDF8" transparent opacity={0.75} />
      </mesh>

      {/* Main North-South Cross-City Boulevard */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]}>
        <planeGeometry args={[3.5, 60]} />
        <meshStandardMaterial color="#1e293b" roughness={0.8} />
      </mesh>

      {/* Boulevard Centerline */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.005, 0]}>
        <planeGeometry args={[0.12, 60]} />
        <meshBasicMaterial color="#10B981" transparent opacity={0.75} />
      </mesh>

      {/* Lucknow Gomti River Water Body Strip */}
      <mesh rotation={[-Math.PI / 2, 0, Math.PI / 8]} position={[-20, 0.01, -20]}>
        <planeGeometry args={[70, 7]} />
        <meshStandardMaterial
          color="#0284c7"
          roughness={0.15}
          metalness={0.8}
          transparent
          opacity={0.85}
        />
      </mesh>

      {/* Riverbank Promenade Neon Edge */}
      <mesh rotation={[-Math.PI / 2, 0, Math.PI / 8]} position={[-20, 0.02, -16.5]}>
        <planeGeometry args={[70, 0.15]} />
        <meshBasicMaterial color="#06B6D4" transparent opacity={0.6} />
      </mesh>

      {/* Janeshwar Mishra Urban Eco-Park Zone */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[16, 0.008, 16]}>
        <planeGeometry args={[14, 14]} />
        <meshStandardMaterial
          color="#064e3b"
          roughness={0.9}
        />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[16, 0.012, 16]}>
        <ringGeometry args={[6.8, 7.0, 32]} />
        <meshBasicMaterial color="#10B981" transparent opacity={0.4} />
      </mesh>

      {/* Cyan & Slate Coordinate Grid */}
      <primitive object={gridHelper} position={[0, 0.02, 0]} />

      {/* Tactical Center Coordinate Radar Perimeter */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.025, 0]}>
        <ringGeometry args={[26.8, 27.1, 64]} />
        <meshBasicMaterial color="#38BDF8" transparent opacity={0.25} side={THREE.DoubleSide} />
      </mesh>
    </>
  );
});

SceneEnvironment.displayName = 'SceneEnvironment';

interface DigitalTwinSceneProps {
  className?: string;
}

export const DigitalTwinSceneInternal: React.FC<DigitalTwinSceneProps> = ({ className = 'w-full h-full' }) => {
  const set3DReady = useUrbanSyncStore((s) => s.set3DReady);
  const surveillanceStatus = useUrbanSyncStore((s) => s.surveillanceStatus);
  const duressTriggered = useUrbanSyncStore((s) => s.duressTriggered);
  const activeEscort = useUrbanSyncStore((s) => s.activeEscort);
  const controlsRef = useRef<OrbitControlsImpl>(null);

  const [cctvVisible, setCctvVisible] = useState(true);
  const [wasteVisible, setWasteVisible] = useState(true);
  const [corridorsVisible, setCorridorsVisible] = useState(true);

  // Notify Zustand store that 3D scene is mounted and ready
  useEffect(() => {
    set3DReady(true);
    return () => set3DReady(false);
  }, [set3DReady]);

  const handleResetCamera = () => {
    if (controlsRef.current) {
      controlsRef.current.reset();
    }
  };

  return (
    <div className={`relative bg-gradient-to-b from-[#0f172a] via-[#111d38] to-[#0a0f1d] select-none ${className}`}>
      {/* Tactical HUD Header Bar with Official Logos */}
      <div className="absolute top-3 left-3 z-10 pointer-events-none flex flex-col gap-1.5 text-xs font-mono">
        <div className="flex items-center gap-2.5 bg-[#0f172a]/95 border border-cyan-500/40 px-3.5 py-2 rounded-lg backdrop-blur-md text-cyan-300 shadow-[0_4px_20px_rgba(6,182,212,0.25)]">
          <LucknowCivicLogo className="w-5 h-5" />
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-extrabold text-white tracking-wider">URBANSYNC DIGITAL TWIN</span>
              <span className="text-slate-500">|</span>
              <span className="text-cyan-400 font-semibold">LUCKNOW SECTOR 4</span>
            </div>
            <span className="text-[10px] text-slate-400">26.85°N, 80.95°E • GIS Isometric Grid</span>
          </div>
        </div>

        {/* Dynamic Threat / Surveillance Status Banner */}
        <div className="flex items-center gap-2">
          <div
            className={`px-3 py-1 rounded-md text-[11px] font-bold border backdrop-blur-md shadow-md ${
              duressTriggered || surveillanceStatus === 'BLIND_SPOT_DETECTED'
                ? 'bg-rose-500/20 border-rose-500 text-rose-300 shadow-rose-500/20 animate-pulse'
                : 'bg-emerald-500/20 border-emerald-500 text-emerald-300 shadow-emerald-500/20'
            }`}
          >
            {duressTriggered
              ? 'CODE-RED P1: DURESS SIGNAL DETECTED'
              : surveillanceStatus === 'BLIND_SPOT_DETECTED'
              ? 'ALERT: SURVEILLANCE BLIND SPOT DETECTED'
              : 'SURVEILLANCE LOCKED: ALL CORRIDORS NOMINAL'}
          </div>

          {activeEscort?.is_active && (
            <div className="px-2.5 py-1 rounded-md text-[11px] font-bold bg-cyan-950/90 border border-cyan-400 text-cyan-300 shadow-md">
              ESCORT MODE: T-{activeEscort.countdown_remaining_sec}s
            </div>
          )}
        </div>
      </div>

      {/* Layer Toggles & Camera Reset HUD */}
      <div className="absolute top-3 right-3 z-10 flex items-center gap-2 font-mono text-xs">
        <button
          onClick={() => setCctvVisible(!cctvVisible)}
          className={`px-3 py-1.5 rounded-lg border font-semibold transition-all cursor-pointer shadow-sm ${
            cctvVisible
              ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 shadow-[0_0_12px_rgba(6,182,212,0.3)]'
              : 'bg-slate-900/80 border-slate-700 text-slate-400 hover:border-slate-500'
          }`}
          title="Toggle CCTV Frustum Cones"
        >
          CCTV {cctvVisible ? '●' : '○'}
        </button>

        <button
          onClick={() => setWasteVisible(!wasteVisible)}
          className={`px-3 py-1.5 rounded-lg border font-semibold transition-all cursor-pointer shadow-sm ${
            wasteVisible
              ? 'bg-amber-500/20 border-amber-400 text-amber-300 shadow-[0_0_12px_rgba(245,158,11,0.3)]'
              : 'bg-slate-900/80 border-slate-700 text-slate-400 hover:border-slate-500'
          }`}
          title="Toggle Smart Waste Nodes"
        >
          WASTE {wasteVisible ? '●' : '○'}
        </button>

        <button
          onClick={() => setCorridorsVisible(!corridorsVisible)}
          className={`px-3 py-1.5 rounded-lg border font-semibold transition-all cursor-pointer shadow-sm ${
            corridorsVisible
              ? 'bg-emerald-500/20 border-emerald-400 text-emerald-300 shadow-[0_0_12px_rgba(16,185,129,0.3)]'
              : 'bg-slate-900/80 border-slate-700 text-slate-400 hover:border-slate-500'
          }`}
          title="Toggle SafePath Emergency Corridors"
        >
          ROUTES {corridorsVisible ? '●' : '○'}
        </button>

        <button
          onClick={handleResetCamera}
          className="px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-700 hover:border-cyan-400 text-slate-300 hover:text-cyan-300 transition-all cursor-pointer font-semibold shadow-sm"
          title="Reset Camera View to Isometric Center"
        >
          RESET
        </button>
      </div>

      {/* Main React Three Fiber Canvas with Modern Daylight Lighting */}
      <Canvas
        camera={{ position: [32, 34, 32], fov: 48 }}
        gl={{
          antialias: true,
          alpha: false,
          powerPreference: 'high-performance',
        }}
        className="w-full h-full"
      >
        <color attach="background" args={['#0f172a']} />

        {/* Illuminated Environment */}
        <SceneEnvironment />

        {/* 3D Extruded City Blocks */}
        <group name="city-buildings">
          {CITY_BUILDINGS.map((building, i) => (
            <BuildingBlock key={building.id} building={building} index={i} />
          ))}
        </group>

        {/* 3D Floating Landmarks */}
        <CityLandmarks />

        {/* Volumetric CCTV Surveillance Cones */}
        {cctvVisible && <VolumetricCones />}

        {/* Dynamic Waste Accumulation Cylinders */}
        {wasteVisible && <WasteExtrusions />}

        {/* SafePath Corridors & Citizen Kinematics */}
        {corridorsVisible && <EmergencyCorridors />}

        {/* Orbit Controls with Smooth Damping */}
        <OrbitControls
          ref={controlsRef}
          enableDamping
          dampingFactor={0.06}
          minDistance={10}
          maxDistance={65}
          maxPolarAngle={Math.PI / 2.3}
          target={[0, 0, 0]}
        />
      </Canvas>

      {/* Bottom Map Legend */}
      <div className="absolute bottom-3 left-3 z-10 pointer-events-none flex items-center gap-3 text-[11px] font-mono">
        <div className="flex items-center gap-3 bg-[#0f172a]/90 border border-slate-800 px-3 py-1.5 rounded-lg backdrop-blur-md text-slate-300 shadow-md">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#06B6D4]" />
            <span>CCTV Frustums</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]" />
            <span>SafePath Corridor</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#F43F5E]" />
            <span>Direct Hazard Route</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-[#F59E0B]" />
            <span>Waste Cylinders</span>
          </span>
        </div>

        <div className="bg-[#0f172a]/90 border border-slate-800 px-3 py-1.5 rounded-lg backdrop-blur-md text-slate-400 font-semibold">
          THREE.JS r161 • DAYLIGHT TWILIGHT SHADING
        </div>
      </div>
    </div>
  );
};

// Export default as dynamic import with ssr: false wrapper component
const DigitalTwinScene = dynamic(
  () => Promise.resolve(DigitalTwinSceneInternal),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full min-h-[500px] flex flex-col items-center justify-center bg-gradient-to-b from-[#0f172a] to-[#0a0f1d] text-[#06B6D4] font-mono select-none">
        <div className="relative flex items-center justify-center mb-4">
          <div className="w-14 h-14 rounded-full border-2 border-[#06B6D4]/20 border-t-[#06B6D4] animate-spin" />
          <div className="absolute w-8 h-8 rounded-full border border-[#10B981]/30 border-b-[#10B981] animate-spin" />
        </div>
        <div className="text-sm font-bold tracking-wider text-cyan-300">
          INITIALIZING 3D SPATIAL DIGITAL TWIN
        </div>
        <div className="text-[11px] text-slate-400 mt-1">
          Loading urban mesh topography, CCTV cones & safe corridors...
        </div>
      </div>
    ),
  }
);

export default DigitalTwinScene;
