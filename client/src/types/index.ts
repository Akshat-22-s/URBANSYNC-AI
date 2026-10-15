// ==========================================
// UrbanSync AI - Core TypeScript Definitions
// Matches Python Pydantic Models 1:1
// ==========================================

// Enums
export type UrgencyState = 'PLENTY_OF_TIME' | 'LEAVE_SOON' | 'LEAVE_NOW' | 'LATE';
export type SurveillanceStatus = 'SURVEILLANCE_LOCKED' | 'BLIND_SPOT_DETECTED' | 'OUT_OF_RANGE';
export type PinType = 'SAFE' | 'DURESS';
export type EscalationCode = 'CODE_GREEN' | 'CODE_RED_P1';
export type EventType =
  | 'WASTE_OVERFLOW'
  | 'SNATCH_ALERT'
  | 'DURESS_TRIGGER'
  | 'VEHICLE_REROUTE'
  | 'GREEN_WAVE'
  | 'JERK_DETECTED';
export type Severity = 'INFO' | 'WARNING' | 'CRITICAL';
export type Department = 'SANITATION' | 'MOBILITY' | 'SAFETY';

// Core Telemetry & Geography
export interface Coordinate {
  lat: number;
  lon: number;
}

export interface WasteNode {
  id: string;
  lat: number;
  lon: number;
  fill_pct: number;
  capacity_kg: number;
  demand_kg: number;
  last_collected: string | null;
}

export interface DynamicBuffer {
  parking_min: number;
  toll_min: number;
  weather_min: number;
  total: number;
}

export interface TripPlanCalculation {
  event_time: string;
  arrive_by: string;
  transit_duration_min: number;
  dynamic_buffer: DynamicBuffer;
  depart_at: string;
  urgency: UrgencyState;
}

export interface RouteInfo {
  route_id: string;
  waypoints: Coordinate[];
  distance_km: number;
  duration_min: number;
  safety_score: number | null;
  color_hex: string;
}

export interface SafePathResult {
  route_a: RouteInfo;
  route_b: RouteInfo;
  surveillance_status: SurveillanceStatus;
  blind_spots: Coordinate[];
}

export interface CitizenTelemetryPacket {
  citizen_id: string;
  lat: number;
  lon: number;
  accel_g: number;
  timestamp: string;
  escort_active: boolean;
  heading_deg: number;
}

export interface EmergencyEscalationPayload {
  citizen_id: string;
  lat: number;
  lon: number;
  pin_type: PinType;
  timestamp: string;
  code: EscalationCode;
}

export interface CVRPSolution {
  vehicle_routes: string[][];
  total_distance_km: number;
  total_demand_served_kg: number;
}

export interface GreenWaveCorridor {
  corridor_id: string;
  intersections: string[];
  speed_kph: number;
  phase_offset_ms: number[];
}

export interface DispatchEvent {
  event_id: string;
  event_type: EventType;
  lat: number;
  lon: number;
  timestamp: string;
  payload: Record<string, unknown>;
  severity: Severity;
}

export interface EscortSession {
  citizen_id: string;
  started_at: string;
  last_heartbeat: string;
  is_active: boolean;
  jerk_detected: boolean;
  countdown_remaining_sec: number;
  origin: Coordinate;
  destination: Coordinate;
}

export interface CCTVCamera {
  camera_id: string;
  lat: number;
  lon: number;
  altitude_m: number;
  heading_deg: number;
  fov_deg: number;
  range_m: number;
}

export interface BuildingBlock {
  block_id: string;
  center_lat: number;
  center_lon: number;
  width_m: number;
  depth_m: number;
  height_m: number;
}

// Store State Definition
export interface UrbanSyncState {
  // Telemetry
  citizens: Record<string, CitizenTelemetryPacket>;
  wasteBins: Record<string, WasteNode>;
  events: DispatchEvent[];
  greenCorridors: GreenWaveCorridor[];

  // Safety
  activeEscort: EscortSession | null;
  surveillanceStatus: SurveillanceStatus;
  duressTriggered: boolean;

  // Mobility
  currentTrip: TripPlanCalculation | null;
  activeRoute: RouteInfo | null;
  safePath: SafePathResult | null;

  // UI state
  selectedDepartment: Department | null;
  timeSliderValue: number; // 0 = T0, 1 = T1, 2 = T2
  is3DReady: boolean;
  cockpitConnected: boolean;
}

// Store Actions Definition
export interface UrbanSyncActions {
  updateCitizen: (packet: CitizenTelemetryPacket) => void;
  updateWasteBin: (node: WasteNode) => void;
  addEvent: (event: DispatchEvent) => void;
  setGreenCorridors: (corridors: GreenWaveCorridor[]) => void;
  startEscort: (session: EscortSession) => void;
  updateEscort: (updates: Partial<EscortSession>) => void;
  endEscort: () => void;
  triggerDuress: (payload: EmergencyEscalationPayload) => void;
  setCurrentTrip: (trip: TripPlanCalculation | null) => void;
  setActiveRoute: (route: RouteInfo | null) => void;
  setSafePath: (result: SafePathResult | null) => void;
  setSelectedDepartment: (dept: Department | null) => void;
  setTimeSlider: (value: number) => void;
  set3DReady: (ready: boolean) => void;
  setCockpitConnected: (connected: boolean) => void;
  reset: () => void;
}

export type UrbanSyncStore = UrbanSyncState & UrbanSyncActions;

// WebSocket Transport Types
export type SocketChannel = 'cockpit' | 'citizen' | 'field-worker';

export type SocketMessageType =
  | 'TELEMETRY_UPDATE'
  | 'WASTE_DELTA'
  | 'GREEN_CORRIDOR'
  | 'SAFETY_ALERT'
  | 'DISPATCH_EVENT';

export interface BaseSocketMessage<T = unknown> {
  type: SocketMessageType;
  payload: T;
  timestamp?: string;
}

export interface TelemetryUpdateMessage extends BaseSocketMessage<CitizenTelemetryPacket> {
  type: 'TELEMETRY_UPDATE';
}

export interface WasteDeltaMessage extends BaseSocketMessage<WasteNode> {
  type: 'WASTE_DELTA';
}

export interface GreenCorridorMessage extends BaseSocketMessage<GreenWaveCorridor[]> {
  type: 'GREEN_CORRIDOR';
}

export interface SafetyAlertMessage extends BaseSocketMessage<EmergencyEscalationPayload | DispatchEvent> {
  type: 'SAFETY_ALERT';
}

export interface DispatchEventSocketMessage extends BaseSocketMessage<DispatchEvent> {
  type: 'DISPATCH_EVENT';
}

export type SocketMessage =
  | TelemetryUpdateMessage
  | WasteDeltaMessage
  | GreenCorridorMessage
  | SafetyAlertMessage
  | DispatchEventSocketMessage;
