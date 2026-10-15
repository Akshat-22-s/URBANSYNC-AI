'use client';

import React, { useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { Line, Html } from '@react-three/drei';
import { useUrbanSyncStore } from '@/store/useUrbanSyncStore';
import {
  DEFAULT_SAFE_PATH,
  geoToScene,
} from './sceneConfig';

const NUM_PARTICLES = 24;

export const EmergencyCorridors: React.FC = () => {
  const safePath = useUrbanSyncStore((s) => s.safePath);
  const activeEscort = useUrbanSyncStore((s) => s.activeEscort);
  const citizens = useUrbanSyncStore((s) => s.citizens);
  const events = useUrbanSyncStore((s) => s.events);
  const duressTriggered = useUrbanSyncStore((s) => s.duressTriggered);

  // References for dynamic animated objects
  const beaconMeshRef = useRef<THREE.Mesh>(null);
  const beaconBeamRef = useRef<THREE.Mesh>(null);
  const shockwaveRef = useRef<THREE.Mesh>(null);
  const shockwaveMatRef = useRef<THREE.MeshBasicMaterial>(null);
  const citizenGroupRef = useRef<THREE.Group>(null);
  const radarRingRef = useRef<THREE.Mesh>(null);
  const particlesGroupRef = useRef<THREE.Group>(null);

  // 1. Resolve Route A Points (Shortest Physical - Dashed Crimson Danger)
  const routeAPoints = useMemo<[number, number, number][]>(() => {
    const rawWaypoints = safePath?.route_a?.waypoints?.length
      ? safePath.route_a.waypoints
      : DEFAULT_SAFE_PATH.route_a.waypoints;

    return rawWaypoints.map((wp) => geoToScene(wp.lat, wp.lon, 0.22));
  }, [safePath]);

  // 2. Resolve Route B Points (SafePath Corridor - Glowing Emerald Safe)
  const routeBPoints = useMemo<[number, number, number][]>(() => {
    const rawWaypoints = safePath?.route_b?.waypoints?.length
      ? safePath.route_b.waypoints
      : DEFAULT_SAFE_PATH.route_b.waypoints;

    return rawWaypoints.map((wp) => geoToScene(wp.lat, wp.lon, 0.22));
  }, [safePath]);

  // Route B Spline Curve for continuous citizen interpolation & escort trail
  const routeBCurve = useMemo(() => {
    const vectors = routeBPoints.map((p) => new THREE.Vector3(p[0], p[1], p[2]));
    return new THREE.CatmullRomCurve3(vectors, false, 'catmullrom', 0.2);
  }, [routeBPoints]);

  // 3. Green Wave Corridor Path & Spline (Central High-Speed Arterial)
  const greenCorridorPoints = useMemo<[number, number, number][]>(() => {
    return [
      [0, 0.26, -22],
      [0, 0.26, -11],
      [0, 0.26, 0],
      [0, 0.26, 11],
      [0, 0.26, 22],
    ];
  }, []);

  const greenWaveCurve = useMemo(() => {
    const vectors = greenCorridorPoints.map((p) => new THREE.Vector3(p[0], p[1], p[2]));
    return new THREE.CatmullRomCurve3(vectors);
  }, [greenCorridorPoints]);

  // 4. Incident Location for Active Emergency Beacon
  const incidentLocation = useMemo<[number, number, number]>(() => {
    // Check if there is a critical event in store
    const criticalEvent = events.find(
      (e) =>
        e.severity === 'CRITICAL' ||
        e.event_type === 'DURESS_TRIGGER' ||
        e.event_type === 'SNATCH_ALERT' ||
        e.event_type === 'JERK_DETECTED'
    );

    if (criticalEvent) {
      return geoToScene(criticalEvent.lat, criticalEvent.lon, 0.5);
    }

    // Default incident location: Blind spot intersection on Route A
    return geoToScene(DEFAULT_SAFE_PATH.blind_spots[0].lat, DEFAULT_SAFE_PATH.blind_spots[0].lon, 0.5);
  }, [events]);

  // Is an active emergency currently in effect?
  const hasActiveEmergency = duressTriggered || events.some((e) => e.severity === 'CRITICAL');

  // Animation frame loop
  useFrame(({ clock }) => {
    const elapsed = clock.getElapsedTime();

    // A. Animate Green Wave Flowing Particles
    if (particlesGroupRef.current) {
      const children = particlesGroupRef.current.children;
      for (let i = 0; i < children.length; i++) {
        const child = children[i];
        // Velocity along curve
        const progress = (elapsed * 0.22 + i / NUM_PARTICLES) % 1.0;
        const pt = greenWaveCurve.getPointAt(progress);
        child.position.set(pt.x, pt.y + 0.1, pt.z);
      }
    }

    // B. Animate Active Emergency Beacon
    if (beaconMeshRef.current) {
      const scale = 1.0 + 0.25 * Math.sin(elapsed * 7);
      beaconMeshRef.current.scale.set(scale, scale, scale);
    }

    if (beaconBeamRef.current) {
      // Pulse light column opacity
      const beamMat = beaconBeamRef.current.material as THREE.MeshBasicMaterial;
      if (beamMat) {
        beamMat.opacity = 0.2 + 0.15 * Math.sin(elapsed * 6);
      }
    }

    if (shockwaveRef.current && shockwaveMatRef.current) {
      // Expanding radar shockwave ring
      const cycle = (elapsed * 1.5) % 1.0;
      const radius = 0.5 + cycle * 3.5;
      shockwaveRef.current.scale.set(radius, radius, 1);
      shockwaveMatRef.current.opacity = (1.0 - cycle) * 0.7;
    }

    // C. Animate Citizen Position & Radar Ring
    if (citizenGroupRef.current) {
      // If live citizen telemetry exists in store, use it; else interpolate smoothly along Route B
      const firstCitizen = Object.values(citizens)[0];
      if (firstCitizen) {
        const [cx, , cz] = geoToScene(firstCitizen.lat, firstCitizen.lon, 0);
        citizenGroupRef.current.position.set(cx, 0.35, cz);
      } else {
        const walkProgress = (elapsed * 0.035) % 1.0;
        const pt = routeBCurve.getPointAt(walkProgress);
        citizenGroupRef.current.position.set(pt.x, 0.35, pt.z);
      }
    }

    if (radarRingRef.current) {
      radarRingRef.current.rotation.z = elapsed * 1.5;
    }
  });

  // Calculate dynamic escort trail points from Route B origin to citizen position
  const escortTrailPoints = useMemo<[number, number, number][]>(() => {
    // 10 intermediate points along Route B for the escort trail
    const trail: [number, number, number][] = [];
    for (let i = 0; i <= 8; i++) {
      const pt = routeBCurve.getPointAt((i / 8) * 0.45);
      trail.push([pt.x, pt.y + 0.05, pt.z]);
    }
    return trail;
  }, [routeBCurve]);

  return (
    <group name="emergency-corridors">
      {/* ======================================================== */}
      {/* 1. ROUTE A: Shortest Physical Path (Dashed Crimson Danger) */}
      {/* ======================================================== */}
      <Line
        points={routeAPoints}
        color="#F43F5E"
        lineWidth={2}
        dashed
        dashSize={0.5}
        gapSize={0.3}
      />

      {/* Route A Route Marker Label */}
      {routeAPoints.length > 2 && (
        <Html
          position={[routeAPoints[2][0], 1.2, routeAPoints[2][2]]}
          center
          distanceFactor={18}
          style={{ pointerEvents: 'none', userSelect: 'none' }}
        >
          <div className="bg-[#060913]/90 border border-rose-500/60 text-rose-400 text-[10px] font-mono font-bold px-2 py-0.5 rounded shadow-lg whitespace-nowrap">
            ROUTE A [HAZARDOUS - BLIND SPOTS]
          </div>
        </Html>
      )}

      {/* ======================================================== */}
      {/* 2. ROUTE B: SafePath Corridor (Solid Glowing Emerald)     */}
      {/* ======================================================== */}
      <Line
        points={routeBPoints}
        color="#10B981"
        lineWidth={3}
      />

      {/* Route B Route Marker Label */}
      {routeBPoints.length > 1 && (
        <Html
          position={[routeBPoints[1][0], 1.2, routeBPoints[1][2]]}
          center
          distanceFactor={18}
          style={{ pointerEvents: 'none', userSelect: 'none' }}
        >
          <div className="bg-[#060913]/90 border border-emerald-500/60 text-emerald-400 text-[10px] font-mono font-bold px-2 py-0.5 rounded shadow-lg whitespace-nowrap">
            ROUTE B [SAFEPATH - CCTV MONITORED]
          </div>
        </Html>
      )}

      {/* ======================================================== */}
      {/* 3. GREEN WAVE CORRIDOR & FLOWING PARTICLES               */}
      {/* ======================================================== */}
      <Line
        points={greenCorridorPoints}
        color="#06B6D4"
        lineWidth={4}
        transparent
        opacity={0.35}
      />

      {/* Flowing High-Speed Emergency Transit Particles */}
      <group ref={particlesGroupRef} name="green-wave-particles">
        {Array.from({ length: NUM_PARTICLES }).map((_, idx) => (
          <mesh key={idx} position={[0, 0.35, -20]}>
            <sphereGeometry args={[0.13, 10, 10]} />
            <meshStandardMaterial
              color="#06B6D4"
              emissive="#10B981"
              emissiveIntensity={0.9}
              roughness={0.1}
            />
          </mesh>
        ))}
      </group>

      {/* Corridor HUD Billboard */}
      <Html
        position={[0, 1.8, 0]}
        center
        distanceFactor={18}
        style={{ pointerEvents: 'none', userSelect: 'none' }}
      >
        <div className="bg-[#060913]/90 border border-cyan-500/60 text-cyan-400 text-[10px] font-mono font-bold px-2 py-0.5 rounded shadow-lg whitespace-nowrap">
          GREEN WAVE TRANSIT CORRIDOR [ACTIVE]
        </div>
      </Html>

      {/* ======================================================== */}
      {/* 4. ACTIVE EMERGENCY BEACON                                */}
      {/* ======================================================== */}
      <group position={incidentLocation} name="emergency-beacon">
        {/* Pulsing Core Red Sphere */}
        <mesh ref={beaconMeshRef} position={[0, 0.4, 0]}>
          <sphereGeometry args={[0.45, 20, 20]} />
          <meshStandardMaterial
            color="#F43F5E"
            emissive="#F43F5E"
            emissiveIntensity={0.8}
            metalness={0.3}
            roughness={0.2}
          />
        </mesh>

        {/* Expanding Ground Shockwave Ring */}
        <mesh ref={shockwaveRef} position={[0, -0.45, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.3, 0.45, 32]} />
          <meshBasicMaterial
            ref={shockwaveMatRef}
            color="#F43F5E"
            transparent
            opacity={0.7}
            side={THREE.DoubleSide}
          />
        </mesh>

        {/* Vertical Translucent Light Column Shooting Up into Sky */}
        <mesh ref={beaconBeamRef} position={[0, 6.0, 0]}>
          <cylinderGeometry args={[0.1, 0.35, 12.0, 16]} />
          <meshBasicMaterial
            color="#F43F5E"
            transparent
            opacity={hasActiveEmergency ? 0.3 : 0.18}
            side={THREE.DoubleSide}
            depthWrite={false}
          />
        </mesh>

        {/* Critical Incident Billboard Badge */}
        <Html
          position={[0, 1.3, 0]}
          center
          distanceFactor={18}
          style={{ pointerEvents: 'none', userSelect: 'none' }}
        >
          <div className="bg-[#060913]/95 border border-rose-500 text-rose-400 text-[10px] font-mono font-bold px-2 py-0.5 rounded shadow-lg whitespace-nowrap animate-pulse">
            {hasActiveEmergency ? 'CRITICAL INCIDENT: CODE-RED P1 DISPATCH' : 'TACTICAL HAZARD: BLIND SPOT AREA'}
          </div>
        </Html>
      </group>

      {/* ======================================================== */}
      {/* 5. ANIMATED CITIZEN MARKER & ESCORT TRAIL                */}
      {/* ======================================================== */}
      <group ref={citizenGroupRef} name="citizen-telemetry-marker">
        {/* Glowing Cyan Citizen Sphere */}
        <mesh position={[0, 0.35, 0]}>
          <sphereGeometry args={[0.3, 18, 18]} />
          <meshStandardMaterial
            color="#06B6D4"
            emissive="#06B6D4"
            emissiveIntensity={0.85}
            roughness={0.1}
            metalness={0.4}
          />
        </mesh>

        {/* Rotating Circular Radar Sensor Ring */}
        <mesh ref={radarRingRef} position={[0, 0.05, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.5, 0.62, 24]} />
          <meshBasicMaterial color="#06B6D4" transparent opacity={0.5} side={THREE.DoubleSide} />
        </mesh>

        {/* Secondary Concentric Range Ring */}
        <mesh position={[0, 0.05, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.85, 0.9, 32]} />
          <meshBasicMaterial color="#10B981" transparent opacity={0.25} side={THREE.DoubleSide} />
        </mesh>

        {/* Citizen Status Billboard Label */}
        <Html
          position={[0, 1.05, 0]}
          center
          distanceFactor={18}
          style={{ pointerEvents: 'none', userSelect: 'none' }}
        >
          <div className="bg-[#060913]/90 border border-cyan-500/60 text-cyan-300 text-[9px] font-mono font-bold px-1.5 py-0.5 rounded shadow-lg whitespace-nowrap">
            {activeEscort?.is_active ? 'CITIZEN-7749 [ESCORT ACTIVE]' : 'CITIZEN-7749 [SAFE]'}
          </div>
        </Html>
      </group>

      {/* Glowing Escort Trail from Origin to Current Citizen Vector */}
      <Line
        points={escortTrailPoints}
        color="#06B6D4"
        lineWidth={3.5}
        transparent
        opacity={0.65}
      />
    </group>
  );
};

export default React.memo(EmergencyCorridors);
