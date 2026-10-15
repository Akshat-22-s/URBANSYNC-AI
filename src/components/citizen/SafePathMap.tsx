'use client';

import React, { useState } from 'react';
import { useUrbanSyncStore } from '@/store/useUrbanSyncStore';
import type { RouteInfo, SurveillanceStatus } from '@/types';
import {
  ShieldCheck,
  AlertTriangle,
  Eye,
  Sun,
  Shield,
  MapPin,
  Clock,
  Compass,
  CheckCircle2,
  Sparkles,
} from 'lucide-react';

interface SafePathMapProps {
  onSelectRoute?: (routeId: 'route_a' | 'route_b') => void;
}

export default function SafePathMap({ onSelectRoute }: SafePathMapProps) {
  const safePath = useUrbanSyncStore((s) => s.safePath);
  const activeRoute = useUrbanSyncStore((s) => s.activeRoute);
  const setActiveRoute = useUrbanSyncStore((s) => s.setActiveRoute);
  const surveillanceStatus = useUrbanSyncStore((s) => s.surveillanceStatus);

  const [selectedRouteId, setSelectedRouteId] = useState<'route_a' | 'route_b'>('route_b');

  // Route A: Shortest Path (Crimson dashed)
  const routeA: RouteInfo = safePath?.route_a || {
    route_id: 'route_a',
    waypoints: [
      { lat: 12.9716, lon: 77.5946 },
      { lat: 12.9742, lon: 77.5988 },
      { lat: 12.9785, lon: 77.6012 },
    ],
    distance_km: 1.4,
    duration_min: 17,
    safety_score: 42,
    color_hex: '#F43F5E',
  };

  // Route B: SafePath Corridor (Emerald solid)
  const routeB: RouteInfo = safePath?.route_b || {
    route_id: 'route_b',
    waypoints: [
      { lat: 12.9716, lon: 77.5946 },
      { lat: 12.973, lon: 77.592 },
      { lat: 12.9765, lon: 77.5955 },
      { lat: 12.9785, lon: 77.6012 },
    ],
    distance_km: 1.8,
    duration_min: 21,
    safety_score: 94,
    color_hex: '#10B981',
  };

  // Blind spots
  const blindSpots = safePath?.blind_spots || [
    { lat: 12.9745, lon: 77.5992 },
    { lat: 12.9768, lon: 77.6001 },
  ];

  const handleRouteSelect = (routeId: 'route_a' | 'route_b') => {
    setSelectedRouteId(routeId);
    const chosen = routeId === 'route_a' ? routeA : routeB;
    setActiveRoute(chosen);
    if (onSelectRoute) {
      onSelectRoute(routeId);
    }
  };

  const getSurveillanceBadge = (status: SurveillanceStatus) => {
    switch (status) {
      case 'SURVEILLANCE_LOCKED':
        return {
          text: 'SURVEILLANCE LOCKED',
          color: 'text-emerald-400',
          bg: 'bg-emerald-500/10 border-emerald-500/30',
          icon: Eye,
        };
      case 'BLIND_SPOT_DETECTED':
        return {
          text: 'BLIND SPOT DETECTED',
          color: 'text-rose-400',
          bg: 'bg-rose-500/10 border-rose-500/30',
          icon: AlertTriangle,
        };
      default:
        return {
          text: 'CALCULATING COVERAGE',
          color: 'text-cyan-400',
          bg: 'bg-cyan-500/10 border-cyan-500/30',
          icon: Compass,
        };
    }
  };

  const statusBadge = getSurveillanceBadge(surveillanceStatus);
  const StatusIcon = statusBadge.icon;

  return (
    <div className="space-y-4">
      {/* Surveillance Status Bar */}
      <div className={`p-3 rounded-xl border flex items-center justify-between ${statusBadge.bg}`}>
        <div className="flex items-center gap-2">
          <StatusIcon className={`w-4 h-4 ${statusBadge.color}`} />
          <span className={`text-xs font-mono font-bold tracking-wider ${statusBadge.color}`}>
            {statusBadge.text}
          </span>
        </div>
        <span className="text-[10px] text-gray-400 font-mono">
          CCTV Corridor AI: Active 32 Nodes
        </span>
      </div>

      {/* Styled Route Map Placeholder Graphic */}
      <div className="relative w-full h-44 rounded-2xl bg-gray-950/90 border border-gray-800 overflow-hidden p-4 flex flex-col justify-between shadow-inner">
        {/* Synthetic Map Grid lines */}
        <div
          className="absolute inset-0 opacity-20 pointer-events-none"
          style={{
            backgroundImage:
              'radial-gradient(circle, #374151 1px, transparent 1px), linear-gradient(to right, rgba(75,85,99,0.15) 1px, transparent 1px), linear-gradient(to bottom, rgba(75,85,99,0.15) 1px, transparent 1px)',
            backgroundSize: '24px 24px',
          }}
        />

        {/* Vector SVG Mock Routes */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none p-4" viewBox="0 0 300 120" preserveAspectRatio="none">
          {/* Route A - Crimson Dashed */}
          <path
            d="M 20,95 Q 120,40 280,25"
            fill="none"
            stroke="#F43F5E"
            strokeWidth="3.5"
            strokeDasharray="6 4"
            className="opacity-90"
          />

          {/* Route B - Emerald Solid with Glow */}
          <path
            d="M 20,95 C 60,110 160,85 280,25"
            fill="none"
            stroke="#10B981"
            strokeWidth="4"
            style={{ filter: 'drop-shadow(0 0 6px rgba(16,185,129,0.8))' }}
          />

          {/* Origin Pin */}
          <circle cx="20" cy="95" r="5" fill="#06B6D4" />
          {/* Destination Pin */}
          <circle cx="280" cy="25" r="5" fill="#10B981" />

          {/* Blind spot warning on Route A */}
          <circle cx="160" cy="50" r="4" fill="#F43F5E" className="animate-ping" />
          <circle cx="160" cy="50" r="3" fill="#F43F5E" />
        </svg>

        {/* Top Badges over map */}
        <div className="relative z-10 flex items-center justify-between text-[10px] font-mono">
          <div className="flex items-center gap-1.5 bg-gray-900/90 border border-gray-700/80 px-2 py-1 rounded-md text-cyan-300">
            <MapPin className="w-3 h-3 text-cyan-400" />
            <span>ORIGIN: Metro Gate 2</span>
          </div>
          <div className="flex items-center gap-1.5 bg-gray-900/90 border border-gray-700/80 px-2 py-1 rounded-md text-emerald-300">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            <span>DEST: Residency Tower</span>
          </div>
        </div>

        {/* Legend on Bottom of Map */}
        <div className="relative z-10 flex items-center justify-between text-[10px] font-mono bg-black/60 backdrop-blur-sm px-2.5 py-1 rounded-lg border border-gray-800">
          <span className="flex items-center gap-1.5 text-rose-400">
            <span className="w-3 h-0.5 border-t-2 border-dashed border-rose-500" /> Route A (Shortest)
          </span>
          <span className="flex items-center gap-1.5 text-emerald-400 font-bold">
            <span className="w-3 h-0.5 bg-emerald-500 shadow-[0_0_6px_#10B981]" /> Route B (SafePath)
          </span>
        </div>
      </div>

      {/* Side-by-side or stacked route comparison cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* Route A Card: Shortest Path */}
        <div
          onClick={() => handleRouteSelect('route_a')}
          className={`cursor-pointer rounded-2xl bg-gray-900/80 backdrop-blur-sm p-4 border transition-all duration-200 relative ${
            selectedRouteId === 'route_a'
              ? 'border-rose-500 shadow-[0_0_18px_rgba(244,63,94,0.3)] bg-gray-900'
              : 'border-dashed border-rose-500/40 hover:border-rose-500/80'
          }`}
        >
          <div className="flex items-start justify-between mb-2">
            <div>
              <span className="text-[10px] font-mono text-rose-400 uppercase tracking-widest font-bold">
                Route A
              </span>
              <h3 className="text-sm font-bold text-gray-100 flex items-center gap-1.5">
                Shortest Direct Path
              </h3>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-rose-500/10 text-rose-400 border border-rose-500/20">
              Low Safety (42/100)
            </span>
          </div>

          <div className="flex items-center gap-3 py-2 text-xs font-mono text-gray-300 border-y border-gray-800">
            <span className="flex items-center gap-1">
              <Compass className="w-3.5 h-3.5 text-rose-400" /> {routeA.distance_km} km
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-rose-400" /> {routeA.duration_min} mins
            </span>
          </div>

          <div className="pt-2 text-[11px] text-gray-400 space-y-1">
            <p className="text-rose-300/90 flex items-center gap-1 text-[10px]">
              <AlertTriangle className="w-3 h-3 text-rose-400 shrink-0" />
              Traverses 2 unlit alleyways with zero CCTV coverage.
            </p>
          </div>

          <button
            onClick={(e) => {
              e.stopPropagation();
              handleRouteSelect('route_a');
            }}
            className={`w-full mt-3 py-2 rounded-xl text-xs font-semibold font-mono transition-all border ${
              selectedRouteId === 'route_a'
                ? 'bg-rose-600 text-white border-rose-500 shadow-md'
                : 'bg-gray-800 text-gray-300 border-gray-700 hover:bg-gray-700'
            }`}
          >
            {selectedRouteId === 'route_a' ? '✓ Route A Selected' : 'Select Shortest Route'}
          </button>
        </div>

        {/* Route B Card: SafePath Corridor (RECOMMENDED) */}
        <div
          onClick={() => handleRouteSelect('route_b')}
          className={`cursor-pointer rounded-2xl bg-gray-900/80 backdrop-blur-sm p-4 border transition-all duration-200 relative ${
            selectedRouteId === 'route_b'
              ? 'border-emerald-500 shadow-[0_0_22px_rgba(16,185,129,0.35)] bg-gray-900'
              : 'border-emerald-500/50 hover:border-emerald-500'
          }`}
        >
          {/* Recommended Badge */}
          <div className="absolute -top-2.5 right-4 px-2 py-0.5 rounded-full bg-emerald-500 text-black text-[9px] font-black uppercase tracking-wider font-mono shadow-[0_0_10px_#10B981] flex items-center gap-1">
            <Sparkles className="w-2.5 h-2.5" />
            RECOMMENDED
          </div>

          <div className="flex items-start justify-between mb-2">
            <div>
              <span className="text-[10px] font-mono text-emerald-400 uppercase tracking-widest font-bold">
                Route B
              </span>
              <h3 className="text-sm font-bold text-gray-100 flex items-center gap-1.5">
                SafePath Corridor
              </h3>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold">
              Safety Score: {routeB.safety_score}/100
            </span>
          </div>

          <div className="flex items-center gap-3 py-2 text-xs font-mono text-gray-300 border-y border-gray-800">
            <span className="flex items-center gap-1">
              <Compass className="w-3.5 h-3.5 text-emerald-400" /> {routeB.distance_km} km
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-emerald-400" /> {routeB.duration_min} mins
            </span>
          </div>

          {/* Safety Score Breakdown factors */}
          <div className="grid grid-cols-2 gap-2 pt-2 text-[10px] font-mono text-gray-300">
            <div className="flex items-center gap-1.5 bg-gray-950/50 p-1.5 rounded-lg border border-gray-800">
              <Sun className="w-3 h-3 text-amber-400" />
              <span>Luminosity: 96%</span>
            </div>
            <div className="flex items-center gap-1.5 bg-gray-950/50 p-1.5 rounded-lg border border-gray-800">
              <Eye className="w-3 h-3 text-cyan-400" />
              <span>CCTV Lock: 100%</span>
            </div>
            <div className="flex items-center gap-1.5 bg-gray-950/50 p-1.5 rounded-lg border border-gray-800">
              <Shield className="w-3 h-3 text-emerald-400" />
              <span>Patrol Proximity: 120m</span>
            </div>
            <div className="flex items-center gap-1.5 bg-gray-950/50 p-1.5 rounded-lg border border-gray-800">
              <ShieldCheck className="w-3 h-3 text-rose-400" />
              <span>Pink Booth: 250m</span>
            </div>
          </div>

          <button
            onClick={(e) => {
              e.stopPropagation();
              handleRouteSelect('route_b');
            }}
            className={`w-full mt-3 py-2 rounded-xl text-xs font-semibold font-mono transition-all border ${
              selectedRouteId === 'route_b'
                ? 'bg-emerald-600 hover:bg-emerald-500 text-white border-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.4)]'
                : 'bg-gray-800 text-gray-300 border-gray-700 hover:bg-gray-700'
            }`}
          >
            {selectedRouteId === 'route_b' ? '✓ Route B Active Corridor' : 'Select SafePath Corridor'}
          </button>
        </div>
      </div>

      {/* List of Detected Blind Spots */}
      {blindSpots.length > 0 && (
        <div className="p-3 rounded-xl bg-gray-950/80 border border-gray-800 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-gray-300 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              Identified Dark Zones & Blind Spots ({blindSpots.length})
            </span>
            <span className="text-[10px] text-gray-400 font-mono">Autonomous Reroute Avoids These</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {blindSpots.map((spot, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between text-[10px] font-mono bg-gray-900/80 p-2 rounded-lg border border-gray-800/80 text-gray-400"
              >
                <span className="flex items-center gap-1 text-rose-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                  Blind Sector #{idx + 1}
                </span>
                <span>
                  {spot.lat.toFixed(4)}, {spot.lon.toFixed(4)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
