'use client';

import { useEffect, useRef, useState, useMemo } from 'react';
import { useUrbanSyncStore } from '@/store/useUrbanSyncStore';
import type { Coordinate, CitizenTelemetryPacket } from '@/types';

export interface KinematicsResult {
  position: Coordinate | null;
  speed_kph: number;
  heading_deg: number;
  accel_g: number;
  isJerkDetected: boolean;
  distanceTraveled_m: number;
  bearingChangeRate_deg_s: number;
}

/**
 * Calculates great-circle distance between two coordinates in meters via Haversine formula.
 */
function calculateDistanceMeters(c1: Coordinate, c2: Coordinate): number {
  const R = 6371000; // Earth's mean radius in meters
  const toRad = Math.PI / 180;
  const dLat = (c2.lat - c1.lat) * toRad;
  const dLon = (c2.lon - c1.lon) * toRad;
  const lat1 = c1.lat * toRad;
  const lat2 = c2.lat * toRad;

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) * Math.sin(dLon / 2);

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * Calculates shortest angular difference between two heading bearings in degrees (-180 to +180).
 */
function angularDifferenceDeg(curr: number, prev: number): number {
  const diff = (curr - prev + 180) % 360 - 180;
  return Math.abs(diff < -180 ? diff + 360 : diff);
}

/**
 * Custom hook to monitor and derive kinematic parameters for a specific citizen
 * based on live telemetry streamed into the Zustand store.
 */
export function useKinematics(citizenId: string): KinematicsResult {
  const telemetry = useUrbanSyncStore((s) => s.citizens[citizenId]);

  const prevTelemetryRef = useRef<CitizenTelemetryPacket | null>(null);
  const distanceAccumulatorRef = useRef<number>(0);
  const lastSpeedKphRef = useRef<number>(0);
  const lastBearingRateRef = useRef<number>(0);

  const [kinematics, setKinematics] = useState<KinematicsResult>({
    position: null,
    speed_kph: 0,
    heading_deg: 0,
    accel_g: 1.0,
    isJerkDetected: false,
    distanceTraveled_m: 0,
    bearingChangeRate_deg_s: 0,
  });

  useEffect(() => {
    if (!telemetry) return;

    const currentPos: Coordinate = { lat: telemetry.lat, lon: telemetry.lon };
    const currentHeading = telemetry.heading_deg ?? 0;
    const currentAccel = telemetry.accel_g ?? 1.0;
    const isJerk = currentAccel > 3.0;

    let computedSpeed = lastSpeedKphRef.current;
    let computedBearingRate = lastBearingRateRef.current;

    if (prevTelemetryRef.current) {
      const prevPos: Coordinate = {
        lat: prevTelemetryRef.current.lat,
        lon: prevTelemetryRef.current.lon,
      };

      const deltaMeters = calculateDistanceMeters(prevPos, currentPos);
      distanceAccumulatorRef.current += deltaMeters;

      // Calculate time delta in seconds
      const prevTime = new Date(prevTelemetryRef.current.timestamp).getTime();
      const currTime = new Date(telemetry.timestamp).getTime();
      const dtSec = Math.max(0.1, (currTime - prevTime) / 1000);

      // Speed in km/h = (meters / seconds) * 3.6
      if (dtSec > 0 && deltaMeters >= 0) {
        computedSpeed = (deltaMeters / dtSec) * 3.6;
        lastSpeedKphRef.current = computedSpeed;
      }

      // Bearing change rate in deg/sec
      const headingDelta = angularDifferenceDeg(currentHeading, prevTelemetryRef.current.heading_deg ?? 0);
      computedBearingRate = headingDelta / dtSec;
      lastBearingRateRef.current = computedBearingRate;
    }

    prevTelemetryRef.current = telemetry;

    setKinematics({
      position: currentPos,
      speed_kph: Number(computedSpeed.toFixed(2)),
      heading_deg: Number(currentHeading.toFixed(1)),
      accel_g: Number(currentAccel.toFixed(2)),
      isJerkDetected: isJerk,
      distanceTraveled_m: Number(distanceAccumulatorRef.current.toFixed(1)),
      bearingChangeRate_deg_s: Number(computedBearingRate.toFixed(2)),
    });
  }, [telemetry]);

  // Memoize fallback if no telemetry yet
  return useMemo(() => {
    if (!telemetry && !kinematics.position) {
      return {
        position: null,
        speed_kph: 0,
        heading_deg: 0,
        accel_g: 1.0,
        isJerkDetected: false,
        distanceTraveled_m: 0,
        bearingChangeRate_deg_s: 0,
      };
    }
    return kinematics;
  }, [telemetry, kinematics]);
}
