'use client';

import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import {
  Clock,
  ShieldAlert,
  Truck,
  Sparkles,
  Layers,
  Cpu,
} from 'lucide-react';
import { useUrbanSyncStore } from '@/store/useUrbanSyncStore';
import { useSocket } from '@/hooks/useSocket';
import DepartmentCards from '@/components/cockpit/DepartmentCards';
import LiveEventStream from '@/components/cockpit/LiveEventStream';
import TimeSlider from '@/components/cockpit/TimeSlider';
import type { Department } from '@/types';
import {
  UrbanSyncLogo,
  LucknowCivicLogo,
  UP112CadLogo,
  ORToolsLogo,
} from '@/components/ui/Logos';

// Dynamic import of 3D Scene with ssr: false
const DigitalTwinScene = dynamic(
  () =>
    import('@/components/3d/DigitalTwinScene').catch(() => {
      return function SceneFallback() {
        return (
          <div className="relative w-full h-full min-h-[520px] rounded-xl border border-slate-800 bg-gradient-to-b from-[#0f172a] via-[#111d38] to-[#0a0f1d] p-6 flex flex-col items-center justify-center overflow-hidden">
            <div className="relative z-10 flex flex-col items-center text-center max-w-md space-y-3">
              <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                <Cpu className="w-6 h-6 animate-pulse" />
              </div>
              <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-widest font-mono">
                Digital Twin 3D Viewport
              </h3>
              <p className="text-xs text-slate-400">
                Loading urban mesh topography, CCTV cones & safe corridors...
              </p>
            </div>
          </div>
        );
      };
    }),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full min-h-[520px] rounded-xl border border-slate-800 bg-[#0f172a] flex flex-col items-center justify-center text-cyan-400 font-mono">
        <div className="w-12 h-12 rounded-full border-2 border-cyan-500/20 border-t-cyan-400 animate-spin mb-3" />
        <span className="text-xs font-semibold tracking-wider text-cyan-300">
          INITIALIZING SPATIAL ACCELERATOR...
        </span>
      </div>
    ),
  }
);

export default function CockpitPage() {
  const { isConnected } = useSocket('cockpit');
  const selectedDepartment = useUrbanSyncStore((s) => s.selectedDepartment);
  const setSelectedDepartment = useUrbanSyncStore((s) => s.setSelectedDepartment);

  // Live real-time clock with hydration-safe mounted state
  const [mounted, setMounted] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<string>('12:00:00');

  useEffect(() => {
    setMounted(true);
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString('en-US', {
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        })
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const departmentTabs: { label: string; value: Department | 'ALL' }[] = [
    { label: 'ALL DEPARTMENTS', value: 'ALL' },
    { label: 'SANITATION', value: 'SANITATION' },
    { label: 'MOBILITY', value: 'MOBILITY' },
    { label: 'SAFETY', value: 'SAFETY' },
  ];

  const handleTabChange = (val: Department | 'ALL') => {
    if (val === 'ALL') {
      setSelectedDepartment(null);
    } else {
      setSelectedDepartment(val);
    }
  };

  const activeTab = selectedDepartment || 'ALL';

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0b1329] via-[#0d1730] to-[#080d1a] text-slate-100 flex flex-col">
      {/* Top Modern Glass Navigation Bar */}
      <header className="sticky top-0 z-50 bg-[#0d162e]/90 backdrop-blur-md border-b border-slate-700/80 px-4 py-2.5 shadow-md">
        <div className="max-w-[1800px] mx-auto flex items-center justify-between gap-4">
          {/* Logo & Platform Name with Official Emblems */}
          <div className="flex items-center gap-3.5">
            <div className="relative group">
              <UrbanSyncLogo className="w-10 h-10 group-hover:scale-105 transition-transform drop-shadow-[0_0_12px_rgba(6,182,212,0.5)]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-black tracking-wider uppercase bg-gradient-to-r from-cyan-400 via-sky-300 to-emerald-400 bg-clip-text text-transparent">
                  UrbanSync AI
                </h1>
                <span className="text-[9px] uppercase px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-400/40 font-mono font-bold tracking-widest">
                  v4.0 META-BUILD
                </span>
                <span className="hidden sm:flex items-center gap-1 text-[10px] text-amber-300 bg-amber-500/10 border border-amber-500/30 px-2 py-0.2 rounded-full font-mono">
                  <Sparkles className="w-3 h-3 text-amber-400" />
                  Daylight 3D Mesh
                </span>
              </div>
              <p className="text-[11px] text-slate-300 font-mono leading-none mt-0.5 flex items-center gap-1.5">
                <span>Autonomous Civic Synchronization & Spatial Twin</span>
                <span className="text-slate-600">•</span>
                <span className="text-emerald-400 font-semibold">Lucknow Smart Grid</span>
              </p>
            </div>
          </div>

          {/* Department Filter Tabs */}
          <div className="flex items-center gap-1 bg-slate-900/90 border border-slate-700/90 p-1 rounded-xl shadow-inner">
            {departmentTabs.map((tab) => {
              const isSelected = activeTab === tab.value;
              return (
                <button
                  key={tab.value}
                  onClick={() => handleTabChange(tab.value)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-gradient-to-r from-cyan-500 to-sky-500 text-slate-950 shadow-[0_0_15px_rgba(6,182,212,0.6)] font-extrabold'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Right Action & Status Area */}
          <div className="flex items-center gap-3">
            {/* Integrated Subsystem Badges */}
            <div className="hidden xl:flex items-center gap-2 border-r border-slate-700 pr-3">
              <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-slate-900/60 border border-slate-800 text-[10px] font-mono text-slate-300" title="Google OR-Tools CVRP Solver">
                <ORToolsLogo className="w-4 h-4" />
                <span>OR-Tools</span>
              </div>
              <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-slate-900/60 border border-slate-800 text-[10px] font-mono text-slate-300" title="UP-112 CAD Emergency Integration">
                <UP112CadLogo className="w-4 h-4" />
                <span>UP-112 CAD</span>
              </div>
            </div>

            {/* Direct navigation links to other companion views */}
            <div className="hidden md:flex items-center gap-2 border-r border-slate-700 pr-3">
              <Link
                href="/citizen"
                className="flex items-center gap-1.5 text-xs font-semibold text-slate-200 hover:text-emerald-300 transition-all px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-700 hover:border-emerald-500/60 hover:shadow-[0_0_12px_rgba(16,185,129,0.3)]"
              >
                <ShieldAlert className="w-3.5 h-3.5 text-emerald-400" />
                <span>Citizen SafePath</span>
              </Link>
              <Link
                href="/field-worker"
                className="flex items-center gap-1.5 text-xs font-semibold text-slate-200 hover:text-cyan-300 transition-all px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-700 hover:border-cyan-500/60 hover:shadow-[0_0_12px_rgba(6,182,212,0.3)]"
              >
                <Truck className="w-3.5 h-3.5 text-cyan-400" />
                <span>Field Fleet</span>
              </Link>
            </div>

            {/* Live Clock */}
            <div className="flex items-center gap-1.5 text-xs font-mono text-slate-200 bg-slate-900/90 px-3 py-1.5 rounded-lg border border-slate-700 shadow-sm">
              <Clock className="w-3.5 h-3.5 text-cyan-400" />
              <span suppressHydrationWarning>{mounted ? currentTime : '12:00:00'}</span>
            </div>

            {/* WebSocket Connection Status Badge */}
            <div
              className={`flex items-center gap-1.5 text-xs font-mono px-3 py-1.5 rounded-lg border transition-all ${
                isConnected
                  ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40 shadow-[0_0_12px_rgba(16,185,129,0.25)]'
                  : 'bg-rose-500/15 text-rose-300 border-rose-500/40 shadow-[0_0_12px_rgba(244,63,94,0.25)]'
              }`}
            >
              {isConnected ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#10B981]" />
                  <span className="font-bold">CAD LIVE</span>
                </>
              ) : (
                <>
                  <span className="w-2 h-2 rounded-full bg-rose-400" />
                  <span className="font-bold">STANDALONE</span>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Grid Viewport */}
      <main className="flex-1 max-w-[1800px] w-full mx-auto p-4">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-full">
          {/* LEFT PANEL (col-span-8): 3D Digital Twin Scene */}
          <section className="lg:col-span-8 flex flex-col min-h-[580px] h-[calc(100vh-6.5rem)] rounded-2xl overflow-hidden bg-[#0f172a]/60 border border-slate-700/80 p-1.5 relative shadow-[0_10px_35px_rgba(0,0,0,0.4)] backdrop-blur-sm">
            <div className="relative w-full h-full rounded-xl overflow-hidden flex flex-col border border-slate-700/50">
              <DigitalTwinScene />
            </div>
          </section>

          {/* RIGHT PANEL (col-span-4): Stacked Operations Column */}
          <section className="lg:col-span-4 flex flex-col gap-3.5 overflow-y-auto max-h-[calc(100vh-6.5rem)] pr-1">
            {/* Department Summary Cards */}
            <DepartmentCards />

            {/* Real-time Scrolling Event Stream */}
            <LiveEventStream />

            {/* Temporal Scrubber Slider */}
            <TimeSlider />
          </section>
        </div>
      </main>
    </div>
  );
}
