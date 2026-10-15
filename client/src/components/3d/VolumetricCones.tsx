'use client';

import React, { useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { useUrbanSyncStore } from '@/store/useUrbanSyncStore';
import {
  SAMPLE_CCTV_CAMERAS,
  CITY_BUILDINGS,
  geoToScene,
  isLineBlockedByBuilding,
} from './sceneConfig';

interface SingleConeProps {
  camera: (typeof SAMPLE_CCTV_CAMERAS)[number];
  citizenPos: [number, number, number];
  isGlobalBlindSpot: boolean;
}

const SingleCameraFrustum: React.FC<SingleConeProps> = React.memo(({ camera, citizenPos, isGlobalBlindSpot }) => {
  const headingRad = (camera.heading_deg * Math.PI) / 180;
  const sweepGroupRef = useRef<THREE.Group>(null);
  const coneMaterialRef = useRef<THREE.MeshStandardMaterial>(null);
  const ringMaterialRef = useRef<THREE.MeshBasicMaterial>(null);
  const ledMaterialRef = useRef<THREE.MeshStandardMaterial>(null);

  // Convert camera coordinates to scene [x, 0, z]
  const [baseX, , baseZ] = useMemo(
    () => geoToScene(camera.lat, camera.lon, 0),
    [camera.lat, camera.lon]
  );
  const poleHeight = camera.altitude_m || 6.5;

  // Cone geometry: radius 3, height 6, 16 segments
  // In Three.js, default ConeGeometry is centered at Y=0 (apex at +3, base at -3).
  // Translating by (0, -3, 0) places apex at local (0, 0, 0) and base at (0, -6, 0).
  const coneGeometry = useMemo(() => {
    const geom = new THREE.ConeGeometry(3, 6, 16, 1, true);
    geom.translate(0, -3, 0);
    return geom;
  }, []);

  // Base circular ring geometry
  const ringGeometry = useMemo(() => {
    return new THREE.RingGeometry(2.88, 3.0, 32);
  }, []);

  // Frame animation: camera sweep oscillation (±5 degrees) & dynamic status detection
  useFrame(({ clock }) => {
    const elapsed = clock.getElapsedTime();
    const sweepAngle = Math.sin(elapsed * 0.85 + camera.sweepOffset) * ((5 * Math.PI) / 180);
    const currentHeading = headingRad + sweepAngle;

    if (sweepGroupRef.current) {
      sweepGroupRef.current.rotation.y = currentHeading;
    }

    // Camera coverage footprint center at ground level (tilt projection forward)
    const tiltForwardOffset = 2.2;
    const footprintX = baseX + Math.sin(currentHeading) * tiltForwardOffset;
    const footprintZ = baseZ + Math.cos(currentHeading) * tiltForwardOffset;

    // Distance from citizen to ground footprint
    const dx = citizenPos[0] - footprintX;
    const dz = citizenPos[2] - footprintZ;
    const distToCitizen = Math.sqrt(dx * dx + dz * dz);
    const isInsideCone = distToCitizen <= 3.4;

    // Check line-of-sight occlusion against buildings
    let isOccluded = false;
    if (isInsideCone) {
      for (const bld of CITY_BUILDINGS) {
        if (isLineBlockedByBuilding(baseX, baseZ, citizenPos[0], citizenPos[2], bld)) {
          isOccluded = true;
          break;
        }
      }
    }

    const inBlindSpot = isInsideCone && (isOccluded || isGlobalBlindSpot);

    // Apply color and opacity changes based on surveillance state
    if (coneMaterialRef.current && ringMaterialRef.current && ledMaterialRef.current) {
      if (inBlindSpot) {
        // Blind spot detected: Flash crimson danger #F43F5E
        const flash = Math.sin(elapsed * 12) > 0 ? 1 : 0.3;
        coneMaterialRef.current.color.set('#F43F5E');
        coneMaterialRef.current.opacity = 0.22 * flash;
        coneMaterialRef.current.emissive.set('#F43F5E');
        coneMaterialRef.current.emissiveIntensity = 0.6 * flash;

        ringMaterialRef.current.color.set('#F43F5E');
        ringMaterialRef.current.opacity = 0.6 * flash;

        ledMaterialRef.current.color.set('#F43F5E');
        ledMaterialRef.current.emissive.set('#F43F5E');
        ledMaterialRef.current.emissiveIntensity = 1.0;
      } else if (isInsideCone) {
        // Inside cone & clear line of sight: Emerald safe #10B981
        coneMaterialRef.current.color.set('#10B981');
        coneMaterialRef.current.opacity = 0.25;
        coneMaterialRef.current.emissive.set('#10B981');
        coneMaterialRef.current.emissiveIntensity = 0.3;

        ringMaterialRef.current.color.set('#10B981');
        ringMaterialRef.current.opacity = 0.5;

        ledMaterialRef.current.color.set('#10B981');
        ledMaterialRef.current.emissive.set('#10B981');
        ledMaterialRef.current.emissiveIntensity = 0.8;
      } else {
        // Default nominal surveillance: Cyber Cyan #06B6D4
        coneMaterialRef.current.color.set('#06B6D4');
        coneMaterialRef.current.opacity = 0.08;
        coneMaterialRef.current.emissive.set('#06B6D4');
        coneMaterialRef.current.emissiveIntensity = 0.05;

        ringMaterialRef.current.color.set('#06B6D4');
        ringMaterialRef.current.opacity = 0.25;

        ledMaterialRef.current.color.set('#06B6D4');
        ledMaterialRef.current.emissive.set('#06B6D4');
        ledMaterialRef.current.emissiveIntensity = 0.4;
      }
    }
  });

  return (
    <group position={[baseX, 0, baseZ]}>
      {/* Structural Camera Pole */}
      <mesh position={[0, poleHeight / 2, 0]}>
        <cylinderGeometry args={[0.07, 0.09, poleHeight, 8]} />
        <meshStandardMaterial color="#1E293B" metalness={0.7} roughness={0.3} />
      </mesh>

      {/* Sweeping Camera Assembly at top of pole */}
      <group position={[0, poleHeight, 0]} ref={sweepGroupRef}>
        {/* Camera Housing */}
        <mesh position={[0, 0, 0]}>
          <boxGeometry args={[0.3, 0.25, 0.45]} />
          <meshStandardMaterial color="#0F172A" metalness={0.8} roughness={0.2} />
        </mesh>

        {/* Optical Lens */}
        <mesh position={[0, -0.05, 0.25]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.09, 0.09, 0.12, 12]} />
          <meshStandardMaterial color="#0284C7" metalness={0.9} roughness={0.1} />
        </mesh>

        {/* Active Telemetry Status LED */}
        <mesh position={[0, 0.14, -0.05]}>
          <sphereGeometry args={[0.05, 8, 8]} />
          <meshStandardMaterial ref={ledMaterialRef} color="#06B6D4" emissive="#06B6D4" emissiveIntensity={0.6} />
        </mesh>

        {/* Volumetric CCTV Surveillance Conical Frustum */}
        {/* Tilting cone slightly forward to project downward onto the street */}
        <group rotation={[0.32, 0, 0]}>
          <mesh geometry={coneGeometry}>
            <meshStandardMaterial
              ref={coneMaterialRef}
              color="#06B6D4"
              transparent
              opacity={0.08}
              side={THREE.DoubleSide}
              depthWrite={false}
              roughness={0.2}
              metalness={0.1}
            />
          </mesh>

          {/* Thin Wireframe Ring at Cone Base */}
          <mesh geometry={ringGeometry} position={[0, -5.98, 0]} rotation={[-Math.PI / 2, 0, 0]}>
            <meshBasicMaterial
              ref={ringMaterialRef}
              color="#06B6D4"
              transparent
              opacity={0.25}
              side={THREE.DoubleSide}
              wireframe={false}
            />
          </mesh>

          {/* Crosshair target indicator at the center of the base */}
          <mesh position={[0, -5.98, 0]} rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.3, 0.35, 16]} />
            <meshBasicMaterial color="#06B6D4" transparent opacity={0.3} side={THREE.DoubleSide} />
          </mesh>
        </group>
      </group>
    </group>
  );
});

SingleCameraFrustum.displayName = 'SingleCameraFrustum';

export const VolumetricCones: React.FC = () => {
  const citizens = useUrbanSyncStore((s) => s.citizens);
  const activeEscort = useUrbanSyncStore((s) => s.activeEscort);
  const surveillanceStatus = useUrbanSyncStore((s) => s.surveillanceStatus);
  const duressTriggered = useUrbanSyncStore((s) => s.duressTriggered);

  // Compute active citizen coordinates in scene space
  const citizenPos = useMemo<[number, number, number]>(() => {
    // Check first citizen packet if available
    const firstCitizen = Object.values(citizens)[0];
    if (firstCitizen) {
      return geoToScene(firstCitizen.lat, firstCitizen.lon, 0);
    }
    // Check active escort destination or origin
    if (activeEscort) {
      return geoToScene(activeEscort.origin.lat, activeEscort.origin.lon, 0);
    }
    // Default safe baseline coordinate (near central boulevard)
    return [0, 0, 5];
  }, [citizens, activeEscort]);

  const isGlobalBlindSpot = surveillanceStatus === 'BLIND_SPOT_DETECTED' || duressTriggered;

  return (
    <group name="volumetric-cctv-cones">
      {SAMPLE_CCTV_CAMERAS.map((cam) => (
        <SingleCameraFrustum
          key={cam.camera_id}
          camera={cam}
          citizenPos={citizenPos}
          isGlobalBlindSpot={isGlobalBlindSpot}
        />
      ))}
    </group>
  );
};

export default React.memo(VolumetricCones);
