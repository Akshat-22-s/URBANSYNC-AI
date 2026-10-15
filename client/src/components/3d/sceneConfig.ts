// ==========================================
// UrbanSync AI - 3D Spatial Digital Twin Configuration
// Center of Lucknow: 26.85° N, 80.95° E
// ==========================================

import type { CCTVCamera, Coordinate, WasteNode, RouteInfo, SafePathResult, GreenWaveCorridor } from '@/types';

export const CENTER_LAT = 26.85;
export const CENTER_LON = 80.95;
export const SCALE_FACTOR = 1000; // 0.01 deg lat/lon ≈ 10 scene units

/**
 * Converts geographical (lat, lon) coordinates to 3D scene (X, Y, Z) coordinates.
 * North corresponds to -Z, East corresponds to +X.
 */
export function geoToScene(lat: number, lon: number, y: number = 0): [number, number, number] {
  const x = (lon - CENTER_LON) * SCALE_FACTOR;
  const z = -(lat - CENTER_LAT) * SCALE_FACTOR;
  return [x, y, z];
}

/**
 * Converts 3D scene (X, Z) coordinates back to geographical (lat, lon).
 */
export function sceneToGeo(x: number, z: number): Coordinate {
  return {
    lat: CENTER_LAT - z / SCALE_FACTOR,
    lon: CENTER_LON + x / SCALE_FACTOR,
  };
}

export interface BuildingData {
  id: string;
  name: string;
  type: 'commercial' | 'residential' | 'civic' | 'police' | 'hospital' | 'infrastructure';
  x: number;
  z: number;
  w: number;
  h: number;
  d: number;
  rotation?: number;
}

// 18 extruded urban building structures arranged in tactical command grid
export const CITY_BUILDINGS: BuildingData[] = [
  // Northwest Quadrant (Commercial & Technology Hub)
  { id: 'bld-01', name: 'Cyber Heights Tower', type: 'commercial', x: -12, z: -14, w: 6, h: 7.5, d: 6 },
  { id: 'bld-02', name: 'Data Center Alpha', type: 'infrastructure', x: -19, z: -14, w: 4.5, h: 4.0, d: 5 },
  { id: 'bld-03', name: 'Metro Tower West', type: 'commercial', x: -12, z: -6, w: 5, h: 6.2, d: 5 },
  { id: 'bld-04', name: 'Municipal Civic Annex', type: 'civic', x: -19, z: -6, w: 4, h: 3.5, d: 4 },

  // Northeast Quadrant (Financial & Corporate District)
  { id: 'bld-05', name: 'Urban Command Citadel', type: 'civic', x: 12, z: -14, w: 6, h: 8.0, d: 6 },
  { id: 'bld-06', name: 'FinTech Hub East', type: 'commercial', x: 19, z: -14, w: 5, h: 5.2, d: 5 },
  { id: 'bld-07', name: 'Retail Galleria', type: 'commercial', x: 12, z: -6, w: 6, h: 4.2, d: 5 },
  { id: 'bld-08', name: 'Metro Interchange East', type: 'infrastructure', x: 19, z: -6, w: 4, h: 3.2, d: 4 },

  // Southwest Quadrant (Healthcare & Residential)
  { id: 'bld-09', name: 'Emergency Trauma Wing', type: 'hospital', x: -12, z: 8, w: 6, h: 5.5, d: 5 },
  { id: 'bld-10', name: 'Apex Pharmacy Block', type: 'hospital', x: -19, z: 8, w: 4, h: 3.8, d: 4 },
  { id: 'bld-11', name: 'Gomti Nagar Heights A', type: 'residential', x: -12, z: 16, w: 5, h: 6.8, d: 5 },
  { id: 'bld-12', name: 'Community Care Hub', type: 'civic', x: -19, z: 16, w: 4, h: 3.0, d: 4 },

  // Southeast Quadrant (Public Safety, Pink Booth & University)
  { id: 'bld-13', name: 'UP 112 Police Command & Pink Booth', type: 'police', x: 12, z: 8, w: 6, h: 5.0, d: 5 },
  { id: 'bld-14', name: 'IoT Telemetry Substation', type: 'infrastructure', x: 19, z: 8, w: 4, h: 4.2, d: 4 },
  { id: 'bld-15', name: 'Smart City Academy', type: 'civic', x: 12, z: 16, w: 5, h: 6.0, d: 5 },
  { id: 'bld-16', name: 'Sanitation Logistics Depot', type: 'infrastructure', x: 19, z: 16, w: 5, h: 3.6, d: 4 },

  // Gate / Boulevard Checkpoints
  { id: 'bld-17', name: 'North Corridor Watchtower', type: 'civic', x: -4, z: -19, w: 3.5, h: 4.5, d: 3.5 },
  { id: 'bld-18', name: 'South Transit Portal', type: 'civic', x: 4, z: 19, w: 3.5, h: 4.8, d: 3.5 },
];

/**
 * Checks whether a 2D line segment between Camera and Citizen intersects a building box (AABB).
 * Used for dynamic blind spot detection.
 */
export function isLineBlockedByBuilding(
  x1: number,
  z1: number,
  x2: number,
  z2: number,
  building: BuildingData
): boolean {
  const minX = building.x - building.w / 2;
  const maxX = building.x + building.w / 2;
  const minZ = building.z - building.d / 2;
  const maxZ = building.z + building.d / 2;

  // Simple Liang-Barsky line clipping against AABB
  let t0 = 0.0;
  let t1 = 1.0;
  const dx = x2 - x1;
  const dz = z2 - z1;

  const p = [-dx, dx, -dz, dz];
  const q = [x1 - minX, maxX - x1, z1 - minZ, maxZ - z1];

  for (let i = 0; i < 4; i++) {
    if (p[i] === 0) {
      if (q[i] < 0) return false; // Parallel and outside
    } else {
      const r = q[i] / p[i];
      if (p[i] < 0) {
        if (r > t1) return false;
        if (r > t0) t0 = r;
      } else {
        if (r < t0) return false;
        if (r < t1) t1 = r;
      }
    }
  }

  return t0 <= t1 && t0 < 0.99 && t1 > 0.01;
}

// 12 Tactical CCTV Cameras placed strategically across Lucknow city sectors
export const SAMPLE_CCTV_CAMERAS: (CCTVCamera & { sweepOffset: number })[] = [
  // Central Boulevard & Pink Booth Surveillance
  { camera_id: 'CAM-LKO-101', lat: sceneToGeo(0, -10).lat, lon: sceneToGeo(0, -10).lon, altitude_m: 7, heading_deg: 180, fov_deg: 60, range_m: 25, sweepOffset: 0.0 },
  { camera_id: 'CAM-LKO-102', lat: sceneToGeo(0, 0).lat, lon: sceneToGeo(0, 0).lon, altitude_m: 7, heading_deg: 0, fov_deg: 60, range_m: 25, sweepOffset: 1.2 },
  { camera_id: 'CAM-LKO-103', lat: sceneToGeo(0, 10).lat, lon: sceneToGeo(0, 10).lon, altitude_m: 7, heading_deg: 180, fov_deg: 60, range_m: 25, sweepOffset: 2.4 },

  // Pink Booth & Police Command Perimeter
  { camera_id: 'CAM-LKO-104', lat: sceneToGeo(7, 8).lat, lon: sceneToGeo(7, 8).lon, altitude_m: 7, heading_deg: 270, fov_deg: 65, range_m: 30, sweepOffset: 0.5 },
  { camera_id: 'CAM-LKO-105', lat: sceneToGeo(12, 3).lat, lon: sceneToGeo(12, 3).lon, altitude_m: 7, heading_deg: 90, fov_deg: 60, range_m: 25, sweepOffset: 1.8 },

  // West Alleyways & Transit Junctions (Route A high-risk shadow zones)
  { camera_id: 'CAM-LKO-106', lat: sceneToGeo(-7, 8).lat, lon: sceneToGeo(-7, 8).lon, altitude_m: 7, heading_deg: 45, fov_deg: 55, range_m: 20, sweepOffset: 3.1 },
  { camera_id: 'CAM-LKO-107', lat: sceneToGeo(-7, -4).lat, lon: sceneToGeo(-7, -4).lon, altitude_m: 7, heading_deg: 135, fov_deg: 50, range_m: 22, sweepOffset: 0.9 },
  { camera_id: 'CAM-LKO-108', lat: sceneToGeo(-14, 0).lat, lon: sceneToGeo(-14, 0).lon, altitude_m: 7, heading_deg: 0, fov_deg: 55, range_m: 20, sweepOffset: 2.1 },

  // East Arterials & Smart Campus
  { camera_id: 'CAM-LKO-109', lat: sceneToGeo(7, -8).lat, lon: sceneToGeo(7, -8).lon, altitude_m: 7, heading_deg: 225, fov_deg: 60, range_m: 25, sweepOffset: 1.4 },
  { camera_id: 'CAM-LKO-110', lat: sceneToGeo(14, 0).lat, lon: sceneToGeo(14, 0).lon, altitude_m: 7, heading_deg: 315, fov_deg: 55, range_m: 25, sweepOffset: 2.7 },
  { camera_id: 'CAM-LKO-111', lat: sceneToGeo(-4, -15).lat, lon: sceneToGeo(-4, -15).lon, altitude_m: 7, heading_deg: 90, fov_deg: 60, range_m: 25, sweepOffset: 0.3 },
  { camera_id: 'CAM-LKO-112', lat: sceneToGeo(4, 15).lat, lon: sceneToGeo(4, 15).lon, altitude_m: 7, heading_deg: 270, fov_deg: 60, range_m: 25, sweepOffset: 1.9 },
];

// 12 Tactical Smart Waste Nodes spread across urban intersections
export const SAMPLE_WASTE_NODES: WasteNode[] = [
  { id: 'W-01', lat: sceneToGeo(-6, -11).lat, lon: sceneToGeo(-6, -11).lon, fill_pct: 35, capacity_kg: 250, demand_kg: 87.5, last_collected: '12:30 IST' },
  { id: 'W-02', lat: sceneToGeo(-6, -3).lat, lon: sceneToGeo(-6, -3).lon, fill_pct: 68, capacity_kg: 200, demand_kg: 136.0, last_collected: '10:15 IST' },
  { id: 'W-03', lat: sceneToGeo(-6, 5).lat, lon: sceneToGeo(-6, 5).lon, fill_pct: 88, capacity_kg: 300, demand_kg: 264.0, last_collected: '08:00 IST' }, // CRITICAL
  { id: 'W-04', lat: sceneToGeo(-6, 13).lat, lon: sceneToGeo(-6, 13).lon, fill_pct: 42, capacity_kg: 200, demand_kg: 84.0, last_collected: '13:45 IST' },
  { id: 'W-05', lat: sceneToGeo(6, -11).lat, lon: sceneToGeo(6, -11).lon, fill_pct: 72, capacity_kg: 250, demand_kg: 180.0, last_collected: '09:20 IST' },
  { id: 'W-06', lat: sceneToGeo(6, -3).lat, lon: sceneToGeo(6, -3).lon, fill_pct: 94, capacity_kg: 350, demand_kg: 329.0, last_collected: '07:30 IST' }, // CRITICAL OVERFLOW
  { id: 'W-07', lat: sceneToGeo(6, 5).lat, lon: sceneToGeo(6, 5).lon, fill_pct: 25, capacity_kg: 200, demand_kg: 50.0, last_collected: '14:10 IST' },
  { id: 'W-08', lat: sceneToGeo(6, 13).lat, lon: sceneToGeo(6, 13).lon, fill_pct: 58, capacity_kg: 300, demand_kg: 174.0, last_collected: '11:05 IST' },
  { id: 'W-09', lat: sceneToGeo(-15, -10).lat, lon: sceneToGeo(-15, -10).lon, fill_pct: 48, capacity_kg: 200, demand_kg: 96.0, last_collected: '13:00 IST' },
  { id: 'W-10', lat: sceneToGeo(-15, 12).lat, lon: sceneToGeo(-15, 12).lon, fill_pct: 82, capacity_kg: 250, demand_kg: 205.0, last_collected: '08:45 IST' }, // CRITICAL
  { id: 'W-11', lat: sceneToGeo(15, -10).lat, lon: sceneToGeo(15, -10).lon, fill_pct: 31, capacity_kg: 250, demand_kg: 77.5, last_collected: '14:30 IST' },
  { id: 'W-12', lat: sceneToGeo(15, 12).lat, lon: sceneToGeo(15, 12).lon, fill_pct: 64, capacity_kg: 200, demand_kg: 128.0, last_collected: '10:50 IST' },
];

// Pre-calculated Tactical SafePath Routes in Lucknow Sector
export const DEFAULT_SAFE_PATH: SafePathResult = {
  route_a: {
    route_id: 'ROUTE_A_SHORTEST_PHYSICAL',
    waypoints: [
      sceneToGeo(-15, 18),
      sceneToGeo(-15, 6),
      sceneToGeo(-7, 6),
      sceneToGeo(-7, -7),
      sceneToGeo(0, -18),
    ],
    distance_km: 1.4,
    duration_min: 17.5,
    safety_score: 42,
    color_hex: '#F43F5E',
  },
  route_b: {
    route_id: 'ROUTE_B_SAFEPATH_CORRIDOR',
    waypoints: [
      sceneToGeo(-15, 18),
      sceneToGeo(0, 18),
      sceneToGeo(0, 0),
      sceneToGeo(0, -18),
    ],
    distance_km: 1.85,
    duration_min: 22.0,
    safety_score: 96,
    color_hex: '#10B981',
  },
  surveillance_status: 'SURVEILLANCE_LOCKED',
  blind_spots: [sceneToGeo(-7, -3), sceneToGeo(-12, 1)],
};

// Default Green Wave Corridor for Emergency Vehicle Routing
export const DEFAULT_GREEN_CORRIDORS: GreenWaveCorridor[] = [
  {
    corridor_id: 'GW-CENTRAL-AVENUE',
    intersections: ['INT-NORTH-GATE', 'INT-CIVIC-SQUARE', 'INT-PINK-BOOTH', 'INT-SOUTH-GATE'],
    speed_kph: 55,
    phase_offset_ms: [0, 4500, 9000, 13500],
  },
];
