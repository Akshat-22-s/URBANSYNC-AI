import { create } from 'zustand';
import type {
  UrbanSyncStore,
  UrbanSyncState,
  CitizenTelemetryPacket,
  WasteNode,
  DispatchEvent,
  GreenWaveCorridor,
  EscortSession,
  EmergencyEscalationPayload,
  TripPlanCalculation,
  RouteInfo,
  SafePathResult,
  Department,
} from '@/types';

const initialState: UrbanSyncState = {
  citizens: {},
  wasteBins: {},
  events: [],
  greenCorridors: [],
  activeEscort: null,
  surveillanceStatus: 'SURVEILLANCE_LOCKED',
  duressTriggered: false,
  currentTrip: null,
  activeRoute: null,
  safePath: null,
  selectedDepartment: null,
  timeSliderValue: 0,
  is3DReady: false,
  cockpitConnected: false,
};

export const useUrbanSyncStore = create<UrbanSyncStore>((set) => ({
  ...initialState,

  updateCitizen: (packet: CitizenTelemetryPacket) =>
    set((state) => {
      const nextCitizens = {
        ...state.citizens,
        [packet.citizen_id]: packet,
      };

      let nextEscort = state.activeEscort;
      let nextEvents = state.events;

      // If this citizen has an active escort session, synchronize telemetry & check for jerk
      if (state.activeEscort && state.activeEscort.citizen_id === packet.citizen_id) {
        const isJerk = packet.accel_g > 3.0;
        nextEscort = {
          ...state.activeEscort,
          last_heartbeat: packet.timestamp,
          jerk_detected: state.activeEscort.jerk_detected || isJerk,
        };

        if (isJerk) {
          const jerkEvent: DispatchEvent = {
            event_id: `jerk-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
            event_type: 'JERK_DETECTED',
            lat: packet.lat,
            lon: packet.lon,
            timestamp: packet.timestamp,
            payload: {
              citizen_id: packet.citizen_id,
              accel_g: packet.accel_g,
              message: 'Severe kinetic jerk / physical assault threshold exceeded (>3.0g)',
            },
            severity: 'CRITICAL',
          };
          nextEvents = [jerkEvent, ...state.events].slice(0, 200);
        }
      }

      return {
        citizens: nextCitizens,
        activeEscort: nextEscort,
        events: nextEvents,
      };
    }),

  updateWasteBin: (node: WasteNode) =>
    set((state) => ({
      wasteBins: {
        ...state.wasteBins,
        [node.id]: node,
      },
    })),

  addEvent: (event: DispatchEvent) =>
    set((state) => ({
      events: [event, ...state.events].slice(0, 200),
    })),

  setGreenCorridors: (corridors: GreenWaveCorridor[]) =>
    set({
      greenCorridors: corridors,
    }),

  startEscort: (session: EscortSession) =>
    set({
      activeEscort: session,
      duressTriggered: false,
      surveillanceStatus: 'SURVEILLANCE_LOCKED',
    }),

  updateEscort: (updates: Partial<EscortSession>) =>
    set((state) => {
      if (!state.activeEscort) return state;
      return {
        activeEscort: {
          ...state.activeEscort,
          ...updates,
        },
      };
    }),

  endEscort: () =>
    set({
      activeEscort: null,
      duressTriggered: false,
      surveillanceStatus: 'SURVEILLANCE_LOCKED',
    }),

  triggerDuress: (payload: EmergencyEscalationPayload) =>
    set((state) => {
      const duressEvent: DispatchEvent = {
        event_id: `evt-duress-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
        event_type: 'DURESS_TRIGGER',
        lat: payload.lat,
        lon: payload.lon,
        timestamp: payload.timestamp || new Date().toISOString(),
        payload: {
          citizen_id: payload.citizen_id,
          pin_type: payload.pin_type,
          code: payload.code,
        },
        severity: 'CRITICAL',
      };

      const nextEscort =
        state.activeEscort && state.activeEscort.citizen_id === payload.citizen_id
          ? { ...state.activeEscort, jerk_detected: true }
          : state.activeEscort;

      return {
        duressTriggered: true,
        surveillanceStatus: 'BLIND_SPOT_DETECTED',
        activeEscort: nextEscort,
        events: [duressEvent, ...state.events].slice(0, 200),
      };
    }),

  setCurrentTrip: (trip: TripPlanCalculation | null) =>
    set({
      currentTrip: trip,
    }),

  setActiveRoute: (route: RouteInfo | null) =>
    set({
      activeRoute: route,
    }),

  setSafePath: (result: SafePathResult | null) =>
    set({
      safePath: result,
      ...(result ? { surveillanceStatus: result.surveillance_status } : {}),
    }),

  setSelectedDepartment: (dept: Department | null) =>
    set({
      selectedDepartment: dept,
    }),

  setTimeSlider: (value: number) =>
    set({
      timeSliderValue: value,
    }),

  set3DReady: (ready: boolean) =>
    set({
      is3DReady: ready,
    }),

  setCockpitConnected: (connected: boolean) =>
    set({
      cockpitConnected: connected,
    }),

  reset: () =>
    set(initialState),
}));
