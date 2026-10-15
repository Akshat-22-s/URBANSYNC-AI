'use client';

import React, { useState, useMemo } from 'react';
import Link from 'next/link';
import { useSocket } from '@/hooks/useSocket';
import { useUrbanSyncStore } from '@/store/useUrbanSyncStore';
import type { WasteNode, TripPlanCalculation, UrgencyState, CVRPSolution } from '@/types';
import {
  Truck,
  Trash2,
  Navigation,
  CheckCircle2,
  Clock,
  Compass,
  ArrowLeft,
  Calendar,
  AlertCircle,
  Battery,
  Fuel,
  MapPin,
  ChevronRight,
  TrendingUp,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { SanitationCoreLogo, ORToolsLogo } from '@/components/ui/Logos';

export default function FieldWorkerPage() {
  const { isConnected, sendMessage } = useSocket('field-worker');
  const wasteBins = useUrbanSyncStore((s) => s.wasteBins);
  const updateWasteBin = useUrbanSyncStore((s) => s.updateWasteBin);
  const currentTrip = useUrbanSyncStore((s) => s.currentTrip);
  const setCurrentTrip = useUrbanSyncStore((s) => s.setCurrentTrip);

  // Initial mock bins if store has none yet
  const initialBinsList: WasteNode[] = useMemo(() => {
    const list = Object.values(wasteBins);
    if (list.length > 0) return list;
    return [
      {
        id: 'BIN-101',
        lat: 12.9716,
        lon: 77.5946,
        fill_pct: 94,
        capacity_kg: 200,
        demand_kg: 188,
        last_collected: null,
      },
      {
        id: 'BIN-102',
        lat: 12.9734,
        lon: 77.5982,
        fill_pct: 82,
        capacity_kg: 200,
        demand_kg: 164,
        last_collected: null,
      },
      {
        id: 'BIN-103',
        lat: 12.9765,
        lon: 77.6021,
        fill_pct: 78,
        capacity_kg: 150,
        demand_kg: 117,
        last_collected: null,
      },
      {
        id: 'BIN-104',
        lat: 12.9798,
        lon: 77.5912,
        fill_pct: 64,
        capacity_kg: 250,
        demand_kg: 160,
        last_collected: '1 hr ago',
      },
      {
        id: 'BIN-105',
        lat: 12.9821,
        lon: 77.5965,
        fill_pct: 45,
        capacity_kg: 200,
        demand_kg: 90,
        last_collected: '2 hrs ago',
      },
      {
        id: 'BIN-106',
        lat: 12.9845,
        lon: 77.6054,
        fill_pct: 88,
        capacity_kg: 300,
        demand_kg: 264,
        last_collected: null,
      },
    ];
  }, [wasteBins]);

  // CVRP Solution State
  const cvrpSolution: CVRPSolution = {
    vehicle_routes: [
      ['DEPOT', 'BIN-101', 'BIN-102', 'BIN-103', 'DEPOT'],
      ['DEPOT', 'BIN-106', 'BIN-104', 'BIN-105', 'DEPOT'],
    ],
    total_distance_km: 18.6,
    total_demand_served_kg: 983,
  };

  // Vehicles list
  const vehicles = [
    {
      id: 'FLEET-ALPHA-01',
      name: 'Electric Compactor #1',
      driver: 'Officer Ramesh K.',
      status: 'En Route Stop #2',
      assignedStops: ['BIN-101', 'BIN-102', 'BIN-103'],
      capacity_kg: 1200,
      currentLoad_kg: 469,
      batteryPct: 82,
      fuelType: 'EV',
    },
    {
      id: 'FLEET-BETA-02',
      name: 'Heavy Hauler #2',
      driver: 'Officer Suresh M.',
      status: 'Loading at BIN-106',
      assignedStops: ['BIN-106', 'BIN-104', 'BIN-105'],
      capacity_kg: 2000,
      currentLoad_kg: 514,
      batteryPct: 67,
      fuelType: 'Hybrid',
    },
  ];

  // Trip Plan Calculator state
  const [mounted, setMounted] = useState<boolean>(false);
  const [eventTimeInput, setEventTimeInput] = useState<string>('18:30');
  const [transitBufferMin, setTransitBufferMin] = useState<number>(35);

  useEffect(() => {
    setMounted(true);
  }, []);

  const calculateTripPlan = (targetTime: string): TripPlanCalculation => {
    const [hours, minutes] = targetTime.split(':').map((v) => parseInt(v, 10));
    const now = mounted ? new Date() : new Date('2026-10-15T12:00:00');
    const targetDate = new Date('2026-10-15T12:00:00');
    targetDate.setHours(hours || 18, minutes || 30, 0, 0);

    const weather_min = 6;
    const toll_min = 4;
    const parking_min = 8;
    const total_buffer = weather_min + toll_min + parking_min; // 18 min
    const transit_duration_min = transitBufferMin; // default 35 min
    const totalTravelTime = transit_duration_min + total_buffer; // 53 min

    const departDate = new Date(targetDate.getTime() - totalTravelTime * 60 * 1000);
    const arriveByDate = new Date(targetDate.getTime() - parking_min * 60 * 1000);

    const diffToDepartMin = Math.round((departDate.getTime() - now.getTime()) / (60 * 1000));

    let urgency: UrgencyState = 'PLENTY_OF_TIME';
    if (diffToDepartMin < 0) {
      urgency = 'LATE';
    } else if (diffToDepartMin <= 10) {
      urgency = 'LEAVE_NOW';
    } else if (diffToDepartMin <= 25) {
      urgency = 'LEAVE_SOON';
    }

    const formatHHMM = (d: Date) => {
      const h = String(d.getHours()).padStart(2, '0');
      const m = String(d.getMinutes()).padStart(2, '0');
      return `${h}:${m}`;
    };

    return {
      event_time: targetTime,
      arrive_by: formatHHMM(arriveByDate),
      transit_duration_min,
      dynamic_buffer: {
        parking_min,
        toll_min,
        weather_min,
        total: total_buffer,
      },
      depart_at: formatHHMM(departDate),
      urgency,
    };
  };

  const calculatedPlan = useMemo(() => {
    return calculateTripPlan(eventTimeInput);
  }, [eventTimeInput, transitBufferMin, mounted]);

  // Handle Mark Bin Collected
  const handleToggleCollect = (bin: WasteNode) => {
    const isCollected = bin.fill_pct === 0;
    const updated: WasteNode = {
      ...bin,
      fill_pct: isCollected ? 85 : 0,
      demand_kg: isCollected ? Math.round(bin.capacity_kg * 0.85) : 0,
      last_collected: isCollected ? null : new Date().toLocaleTimeString(),
    };

    updateWasteBin(updated);

    sendMessage({
      type: 'WASTE_DELTA',
      payload: updated,
    });
  };

  const getUrgencyBadge = (urgency: UrgencyState) => {
    switch (urgency) {
      case 'LEAVE_NOW':
        return {
          label: 'LEAVE NOW',
          color: 'bg-rose-500/20 text-rose-400 border-rose-500/40 animate-pulse',
        };
      case 'LEAVE_SOON':
        return {
          label: 'LEAVE SOON',
          color: 'bg-amber-500/20 text-amber-400 border-amber-500/40',
        };
      case 'LATE':
        return {
          label: 'OVERDUE / LATE',
          color: 'bg-red-700/30 text-red-300 border-red-600/50',
        };
      case 'PLENTY_OF_TIME':
      default:
        return {
          label: 'ON SCHEDULE',
          color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
        };
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0b1329] via-[#0e1935] to-[#080d1a] text-slate-100 flex flex-col">
      {/* Top Header */}
      <header className="sticky top-0 z-40 bg-[#0d162e]/95 backdrop-blur-md border-b border-slate-700/80 px-4 py-3 shadow-md">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex items-center gap-1 text-xs text-slate-300 hover:text-white transition-colors p-2 rounded-xl bg-slate-800/80 border border-slate-700"
            >
              <ArrowLeft className="w-4 h-4 text-cyan-400" />
              <span className="font-mono font-bold">Cockpit</span>
            </Link>

            <div className="flex items-center gap-2.5">
              <SanitationCoreLogo className="w-8 h-8" />
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-sm font-black uppercase tracking-wider text-white">
                    Field Operations & Fleet Dispatch
                  </h1>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-400/40 font-mono font-bold">
                    CVRP Solved
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 font-mono">
                  Real-Time Route Telematics • Google OR-Tools Capacitated Multi-Vehicle Engine
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900/80 border border-slate-700 text-xs font-mono text-slate-300">
              <ORToolsLogo className="w-4 h-4" />
              <span>OR-Tools CVRP</span>
            </div>

            <div
              className={`flex items-center gap-1.5 text-xs font-mono px-3 py-1 rounded-full border ${
                isConnected
                  ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40 shadow-sm font-bold'
                  : 'bg-rose-500/15 text-rose-300 border-rose-500/40 shadow-sm font-bold'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
                }`}
              />
              <span>{isConnected ? 'FLEET SYNC ACTIVE' : 'TELEMETRY DISCONNECTED'}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Field Dashboard Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 space-y-6">
        {/* Next Stop Navigation HUD Banner */}
        <section className="bg-gradient-to-r from-gray-900 via-gray-900/90 to-cyan-950/40 rounded-2xl border border-cyan-500/30 p-4 shadow-xl flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3 w-full md:w-auto">
            <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shrink-0">
              <Navigation className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold uppercase">
                  Next Stop Navigation
                </span>
                <span className="text-xs text-gray-400 font-mono">Sequence #2 of 6</span>
              </div>
              <h2 className="text-base font-bold text-white mt-0.5">
                Target: BIN-101 (Sector 4 Main Road)
              </h2>
              <p className="text-xs text-gray-400 font-mono flex items-center gap-3 mt-0.5">
                <span>Distance: <strong className="text-cyan-400">420m</strong></span>
                <span>•</span>
                <span>ETA: <strong className="text-emerald-400">3 mins (Signal Green Wave Locked)</strong></span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto justify-end">
            <button
              onClick={() => {
                const target = initialBinsList.find((b) => b.id === 'BIN-101');
                if (target) handleToggleCollect(target);
              }}
              className="py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-bold transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)] flex items-center gap-2 active:scale-95 cursor-pointer"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Confirm Pickup at Bin #101</span>
            </button>
          </div>
        </section>

        {/* Top Grid: CVRP Optimization Summary & Vehicle Cards */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* CVRP Route Optimization Display (col-span-5) */}
          <div className="lg:col-span-5 bg-gray-900/80 backdrop-blur-sm border border-gray-800 rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-200">
                  CVRP Optimization Engine
                </h3>
              </div>
              <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">
                OR-Tools Synced
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="bg-gray-950/60 p-3 rounded-xl border border-gray-800">
                <span className="text-[10px] text-gray-400 font-mono uppercase">Total Distance</span>
                <p className="text-xl font-black font-mono text-white mt-1">
                  {cvrpSolution.total_distance_km} <span className="text-xs text-cyan-400 font-normal">km</span>
                </p>
              </div>
              <div className="bg-gray-950/60 p-3 rounded-xl border border-gray-800">
                <span className="text-[10px] text-gray-400 font-mono uppercase">Demand Served</span>
                <p className="text-xl font-black font-mono text-emerald-400 mt-1">
                  {cvrpSolution.total_demand_served_kg} <span className="text-xs text-emerald-300 font-normal">kg</span>
                </p>
              </div>
            </div>

            {/* Vehicle Routes Waypoints Breakdown */}
            <div className="space-y-2 pt-2">
              <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide">
                Optimal Multi-Vehicle Tours:
              </span>
              {cvrpSolution.vehicle_routes.map((tour, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-gray-950/50 border border-gray-800 space-y-1.5"
                >
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-cyan-400 font-bold">Tour #{idx + 1} ({tour.length - 2} Pickups)</span>
                    <span className="text-gray-400 text-[10px]">Depot Return Included</span>
                  </div>
                  <div className="flex items-center gap-1 flex-wrap text-[10px] font-mono text-gray-300">
                    {tour.map((stop, sIdx) => (
                      <React.Fragment key={sIdx}>
                        <span
                          className={`px-1.5 py-0.5 rounded border ${
                            stop === 'DEPOT'
                              ? 'bg-gray-800 text-gray-400 border-gray-700'
                              : 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30'
                          }`}
                        >
                          {stop}
                        </span>
                        {sIdx < tour.length - 1 && (
                          <ChevronRight className="w-3 h-3 text-gray-400 shrink-0" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Vehicle Assignment Cards (col-span-7) */}
          <div className="lg:col-span-7 space-y-3">
            <div className="flex items-center justify-between px-1">
              <h3 className="text-xs font-bold uppercase tracking-wider text-gray-300 flex items-center gap-2">
                <Truck className="w-4 h-4 text-emerald-400" />
                Active Fleet Assignments ({vehicles.length} Units)
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {vehicles.map((v) => (
                <div
                  key={v.id}
                  className="bg-gray-900/80 backdrop-blur-sm border border-gray-800 hover:border-gray-700 rounded-2xl p-4 space-y-3 transition-all"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-widest">
                        {v.id}
                      </span>
                      <h4 className="text-sm font-bold text-white">{v.name}</h4>
                      <p className="text-xs text-gray-400">{v.driver}</p>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      {v.status}
                    </span>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-[11px] text-gray-400 font-mono">
                      <span>Payload Load</span>
                      <span>
                        {v.currentLoad_kg} / {v.capacity_kg} kg ({Math.round((v.currentLoad_kg / v.capacity_kg) * 100)}%)
                      </span>
                    </div>
                    <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full"
                        style={{ width: `${(v.currentLoad_kg / v.capacity_kg) * 100}%` }}
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-gray-800 text-xs font-mono text-gray-400">
                    <span className="flex items-center gap-1.5">
                      <Battery className="w-4 h-4 text-emerald-400" /> {v.batteryPct}% Battery
                    </span>
                    <span className="text-[10px] text-gray-400">
                      Assigned: {v.assignedStops.join(', ')}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Bottom Section: Bin Collection Checklist & Trip Plan Calculator */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* Bin Collection Checklist with Fill Levels (col-span-7) */}
          <div className="lg:col-span-7 bg-gray-900/80 backdrop-blur-sm border border-gray-800 rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Trash2 className="w-4 h-4 text-emerald-400" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-200">
                  Municipal Bin Collection Manifest
                </h3>
              </div>
              <span className="text-[10px] font-mono text-gray-400">
                Click checkbox to record pickup
              </span>
            </div>

            <div className="divide-y divide-gray-800/80">
              {initialBinsList.map((bin) => {
                const isOver75 = bin.fill_pct >= 75;
                const isCollected = bin.fill_pct === 0;

                return (
                  <div
                    key={bin.id}
                    className="py-3 flex items-center justify-between gap-4 hover:bg-gray-800/30 px-2 rounded-xl transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => handleToggleCollect(bin)}
                        className={`w-6 h-6 rounded-lg border flex items-center justify-center transition-all cursor-pointer ${
                          isCollected
                            ? 'bg-emerald-500 border-emerald-400 text-black shadow-[0_0_8px_#10B981]'
                            : 'bg-gray-800 border-gray-700 text-transparent hover:border-gray-500'
                        }`}
                        title={isCollected ? 'Mark as Uncollected' : 'Mark as Collected'}
                      >
                        <CheckCircle2 className="w-4 h-4 stroke-[3]" />
                      </button>

                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-gray-100">
                            {bin.id}
                          </span>
                          {isOver75 && (
                            <span className="px-1.5 py-0.2 rounded text-[9px] font-mono bg-rose-500/20 text-rose-400 border border-rose-500/40 uppercase">
                              CRITICAL FILL
                            </span>
                          )}
                        </div>
                        <span className="text-[11px] text-gray-400 font-mono">
                          {bin.lat.toFixed(4)}° N, {bin.lon.toFixed(4)}° E • Cap: {bin.capacity_kg}kg
                        </span>
                      </div>
                    </div>

                    {/* Progress Bar & Numeric Fill */}
                    <div className="flex items-center gap-4 w-44">
                      <div className="flex-1">
                        <div className="flex justify-between text-[10px] font-mono mb-1">
                          <span className="text-gray-400">Fill Level</span>
                          <span
                            className={`font-bold ${
                              isOver75
                                ? 'text-rose-400'
                                : bin.fill_pct > 50
                                ? 'text-amber-400'
                                : 'text-emerald-400'
                            }`}
                          >
                            {bin.fill_pct}%
                          </span>
                        </div>
                        <div className="h-2 w-full bg-gray-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-300 ${
                              isOver75
                                ? 'bg-rose-500'
                                : bin.fill_pct > 50
                                ? 'bg-amber-500'
                                : 'bg-emerald-500'
                            }`}
                            style={{ width: `${bin.fill_pct}%` }}
                          />
                        </div>
                      </div>

                      <span className="text-[10px] text-gray-400 font-mono w-16 text-right">
                        {bin.demand_kg} kg
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Trip Plan Calculator: Departure Recommendation (col-span-5) */}
          <div className="lg:col-span-5 bg-gray-900/80 backdrop-blur-sm border border-gray-800 rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-200">
                  Dynamic Trip Departure Planner
                </h3>
              </div>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${getUrgencyBadge(calculatedPlan.urgency).color}`}>
                {getUrgencyBadge(calculatedPlan.urgency).label}
              </span>
            </div>

            <p className="text-xs text-gray-400">
              Calculates optimal departure time with multi-factor congestion, parking delays, and weather buffering.
            </p>

            {/* Input Form Controls */}
            <div className="space-y-3 pt-1">
              <div>
                <label className="text-[11px] font-mono text-gray-300 block mb-1">
                  Target Destination / Event Time (HH:MM):
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="time"
                    value={eventTimeInput}
                    onChange={(e) => setEventTimeInput(e.target.value)}
                    className="bg-gray-950 border border-gray-700 rounded-xl px-3 py-2 text-sm font-mono text-white focus:outline-none focus:border-cyan-400 w-full"
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-[11px] font-mono text-gray-300 mb-1">
                  <span>Transit Duration Estimate:</span>
                  <span className="text-cyan-400 font-bold">{transitBufferMin} mins</span>
                </div>
                <input
                  type="range"
                  min={10}
                  max={90}
                  step={5}
                  value={transitBufferMin}
                  onChange={(e) => setTransitBufferMin(parseInt(e.target.value, 10))}
                  aria-label="Transit duration estimate"
                  className="w-full accent-cyan-400 cursor-pointer"
                />
              </div>
            </div>

            {/* Output Departure Recommendation Card */}
            <div className="bg-gradient-to-br from-cyan-950/40 via-gray-950 to-gray-900 border border-cyan-500/30 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-gray-400 uppercase">Recommended Departure</span>
                <span className="text-2xl font-black font-mono text-cyan-400 tracking-tight">
                  {calculatedPlan.depart_at}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 pt-2 border-t border-gray-800 text-center font-mono">
                <div className="bg-gray-900/60 p-2 rounded-lg">
                  <span className="text-[9px] text-gray-400 block">Transit</span>
                  <span className="text-xs font-bold text-gray-200">{calculatedPlan.transit_duration_min}m</span>
                </div>
                <div className="bg-gray-900/60 p-2 rounded-lg">
                  <span className="text-[9px] text-gray-400 block">Dynamic Buffer</span>
                  <span className="text-xs font-bold text-amber-400">+{calculatedPlan.dynamic_buffer.total}m</span>
                </div>
                <div className="bg-gray-900/60 p-2 rounded-lg">
                  <span className="text-[9px] text-gray-400 block">Arrive By</span>
                  <span className="text-xs font-bold text-emerald-400">{calculatedPlan.arrive_by}</span>
                </div>
              </div>

              {/* Breakdown detail tags */}
              <div className="flex items-center justify-between text-[10px] font-mono text-gray-400 pt-1">
                <span>Weather: +{calculatedPlan.dynamic_buffer.weather_min}m</span>
                <span>•</span>
                <span>Toll Gates: +{calculatedPlan.dynamic_buffer.toll_min}m</span>
                <span>•</span>
                <span>Parking: +{calculatedPlan.dynamic_buffer.parking_min}m</span>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
