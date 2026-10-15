'use client';

import React from 'react';
import { ArrowUpRight, Activity } from 'lucide-react';
import { useUrbanSyncStore } from '@/store/useUrbanSyncStore';
import type { Department } from '@/types';
import { SanitationCoreLogo, MobilitySilnLogo, NirbhayaSafetyLogo } from '../ui/Logos';

export default function DepartmentCards() {
  const selectedDepartment = useUrbanSyncStore((s) => s.selectedDepartment);
  const setSelectedDepartment = useUrbanSyncStore((s) => s.setSelectedDepartment);
  const wasteBins = useUrbanSyncStore((s) => s.wasteBins);
  const events = useUrbanSyncStore((s) => s.events);
  const greenCorridors = useUrbanSyncStore((s) => s.greenCorridors);
  const activeEscort = useUrbanSyncStore((s) => s.activeEscort);
  const surveillanceStatus = useUrbanSyncStore((s) => s.surveillanceStatus);

  // Compute live metrics from store
  const binValues = Object.values(wasteBins);
  const binsOver75 = binValues.filter((b) => b.fill_pct >= 75).length;
  const totalBins = binValues.length || 18;
  const totalWasteCollectedKg = binValues.reduce((sum, b) => sum + (b.capacity_kg * (b.fill_pct / 100)), 420);

  // Mobility metrics
  const rerouteEvents = events.filter((e) => e.event_type === 'VEHICLE_REROUTE').length;
  const activeCorridorsCount = greenCorridors.length || 4;
  const avgCongestionFactor = (1.24 + (rerouteEvents * 0.05)).toFixed(2);

  // Safety metrics
  const safetyEventsCount = events.filter((e) =>
    ['SNATCH_ALERT', 'DURESS_TRIGGER', 'JERK_DETECTED'].includes(e.event_type)
  ).length;
  const activeEscortsCount = activeEscort ? 1 : 0;
  const surveillanceCoveragePct = surveillanceStatus === 'SURVEILLANCE_LOCKED' ? 98.4 : 84.2;

  const handleCardClick = (dept: Department) => {
    if (selectedDepartment === dept) {
      setSelectedDepartment(null);
    } else {
      setSelectedDepartment(dept);
    }
  };

  const departments: {
    id: Department;
    name: string;
    subtext: string;
    LogoComponent: React.ComponentType<{ className?: string }>;
    accentColor: string;
    glowClass: string;
    borderClass: string;
    badgeBg: string;
    progressPct: number;
    incidentsCount: number;
    metrics: { label: string; value: string | number }[];
    status: string;
  }[] = [
    {
      id: 'SANITATION',
      name: 'Sanitation Core',
      subtext: 'CVRP Logistics • OR-Tools',
      LogoComponent: SanitationCoreLogo,
      accentColor: '#10B981',
      glowClass: 'hover:shadow-[0_4px_25px_rgba(16,185,129,0.3)] hover:border-emerald-400/80',
      borderClass: selectedDepartment === 'SANITATION'
        ? 'border-emerald-400 bg-[#10b981]/10 shadow-[0_0_20px_rgba(16,185,129,0.35)]'
        : 'border-slate-700/80 hover:border-emerald-500/60',
      badgeBg: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40',
      progressPct: Math.min(100, Math.round((binsOver75 / totalBins) * 100) + 25),
      incidentsCount: binsOver75,
      metrics: [
        { label: 'Bins > 75%', value: `${binsOver75} / ${totalBins}` },
        { label: 'Active Fleet', value: '12 Trucks' },
        { label: 'Collected', value: `${(totalWasteCollectedKg / 1000).toFixed(1)}t` },
      ],
      status: binsOver75 > 5 ? 'High Demand' : 'Optimal Wave',
    },
    {
      id: 'MOBILITY',
      name: 'SILN Mobility',
      subtext: 'LogPose • Green Waves',
      LogoComponent: MobilitySilnLogo,
      accentColor: '#06B6D4',
      glowClass: 'hover:shadow-[0_4px_25px_rgba(6,182,212,0.3)] hover:border-cyan-400/80',
      borderClass: selectedDepartment === 'MOBILITY'
        ? 'border-cyan-400 bg-[#06b6d4]/10 shadow-[0_0_20px_rgba(6,182,212,0.35)]'
        : 'border-slate-700/80 hover:border-cyan-500/60',
      badgeBg: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/40',
      progressPct: 88,
      incidentsCount: rerouteEvents,
      metrics: [
        { label: 'Reroutes', value: rerouteEvents },
        { label: 'Green Waves', value: `${activeCorridorsCount} Synced` },
        { label: 'Congestion', value: `${avgCongestionFactor}x` },
      ],
      status: rerouteEvents > 2 ? 'Congested' : 'Synchronized',
    },
    {
      id: 'SAFETY',
      name: 'Nirbhaya-Mesh',
      subtext: 'SafePath v3.7 • UP-112 CAD',
      LogoComponent: NirbhayaSafetyLogo,
      accentColor: '#F43F5E',
      glowClass: 'hover:shadow-[0_4px_25px_rgba(244,63,94,0.3)] hover:border-rose-400/80',
      borderClass: selectedDepartment === 'SAFETY'
        ? 'border-rose-400 bg-[#f43f5e]/10 shadow-[0_0_20px_rgba(244,63,94,0.35)]'
        : 'border-slate-700/80 hover:border-rose-500/60',
      badgeBg: 'bg-rose-500/15 text-rose-300 border-rose-500/40',
      progressPct: Math.round(surveillanceCoveragePct),
      incidentsCount: safetyEventsCount,
      metrics: [
        { label: 'Escorts', value: `${activeEscortsCount} Active` },
        { label: 'CCTV Lock', value: `${surveillanceCoveragePct}%` },
        { label: 'Alerts', value: safetyEventsCount },
      ],
      status: safetyEventsCount > 0 ? 'Alert Active' : 'Nominal Lock',
    },
  ];

  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between text-xs px-1">
        <span className="text-slate-300 uppercase tracking-wider font-bold flex items-center gap-1.5 font-mono">
          <Activity className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
          Autonomous Subsystems Operational Feed
        </span>
        {selectedDepartment && (
          <button
            onClick={() => setSelectedDepartment(null)}
            className="text-xs text-cyan-400 hover:text-cyan-300 underline font-mono cursor-pointer font-semibold"
          >
            Clear Filter (Show All)
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        {departments.map((dept) => {
          const Logo = dept.LogoComponent;
          const isSelected = selectedDepartment === dept.id;

          return (
            <div
              key={dept.id}
              onClick={() => handleCardClick(dept.id)}
              className={`relative group cursor-pointer rounded-xl bg-[#131d35]/90 backdrop-blur-md p-3.5 border transition-all duration-300 ${dept.borderClass} ${dept.glowClass} flex flex-col justify-between shadow-lg`}
            >
              {/* Top Row: Official Logo + Header + Status Badge */}
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2.5">
                  <div className="p-1 rounded-lg bg-slate-900/60 border border-slate-700/60 group-hover:scale-105 transition-transform">
                    <Logo className="w-7 h-7" />
                  </div>
                  <div>
                    <h3 className="text-xs font-black text-white group-hover:text-cyan-300 transition-colors leading-tight">
                      {dept.name}
                    </h3>
                    <p className="text-[10px] text-slate-400 font-mono leading-none mt-0.5">
                      {dept.subtext}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-1.5">
                  {dept.incidentsCount > 0 && (
                    <span className="flex h-2 w-2 relative">
                      <span
                        className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
                        style={{ backgroundColor: dept.accentColor }}
                      />
                      <span
                        className="relative inline-flex rounded-full h-2 w-2"
                        style={{ backgroundColor: dept.accentColor }}
                      />
                    </span>
                  )}
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full border font-mono font-bold ${dept.badgeBg}`}
                  >
                    {dept.incidentsCount} Incidents
                  </span>
                </div>
              </div>

              {/* Progress Indicator Bar */}
              <div className="w-full bg-slate-900/80 rounded-full h-1.5 my-1.5 overflow-hidden border border-slate-800">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${dept.progressPct}%`,
                    backgroundColor: dept.accentColor,
                    boxShadow: `0 0 8px ${dept.accentColor}`,
                  }}
                />
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-3 gap-1 py-1.5 my-1 border-y border-slate-700/60 text-center bg-slate-900/40 rounded-lg">
                {dept.metrics.map((m, idx) => (
                  <div key={idx} className="flex flex-col px-1">
                    <span className="text-[9px] text-slate-400 font-medium truncate">{m.label}</span>
                    <span className="text-[11px] font-extrabold text-slate-100 font-mono tracking-tight">{m.value}</span>
                  </div>
                ))}
              </div>

              {/* Bottom Row: Status Tag & Selection State */}
              <div className="flex items-center justify-between pt-1 text-[10px] font-mono">
                <span className="text-slate-300 font-semibold flex items-center gap-1.5">
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: dept.accentColor }}
                  />
                  {dept.status}
                </span>

                <span className="text-cyan-400 group-hover:text-cyan-300 font-bold flex items-center">
                  {isSelected ? 'FILTERED' : 'SELECT'}
                  <ArrowUpRight className="w-3 h-3 ml-0.5 opacity-70 group-hover:opacity-100" />
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
