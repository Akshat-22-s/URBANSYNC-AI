'use client';

import React, { useEffect, useRef, useState, useMemo } from 'react';
import { useUrbanSyncStore } from '@/store/useUrbanSyncStore';
import type { DispatchEvent, Severity, Department } from '@/types';
import { Radio, ArrowDown, MapPin } from 'lucide-react';
import { SanitationCoreLogo, MobilitySilnLogo, NirbhayaSafetyLogo } from '../ui/Logos';

export default function LiveEventStream() {
  const events = useUrbanSyncStore((s) => s.events);
  const selectedDepartment = useUrbanSyncStore((s) => s.selectedDepartment);
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const [autoScroll, setAutoScroll] = useState<boolean>(true);

  const [mounted, setMounted] = useState<boolean>(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Map event types to departments for filtering
  const eventDepartmentMap: Record<string, Department> = {
    WASTE_OVERFLOW: 'SANITATION',
    SNATCH_ALERT: 'SAFETY',
    DURESS_TRIGGER: 'SAFETY',
    JERK_DETECTED: 'SAFETY',
    VEHICLE_REROUTE: 'MOBILITY',
    GREEN_WAVE: 'MOBILITY',
  };

  // Seed events with fixed deterministic timestamps to guarantee SSR and CSR hydration parity
  const displayEvents = useMemo(() => {
    let list = events;
    if (list.length === 0) {
      list = [
        {
          event_id: 'seed-1',
          event_type: 'WASTE_OVERFLOW',
          lat: 26.8467,
          lon: 80.9462,
          timestamp: '2026-10-15T10:00:00.000Z',
          payload: { message: 'Smart Bin #42 (Hazratganj) reached 94% volume. Dispatching Compactor Unit 3.' },
          severity: 'WARNING',
        },
        {
          event_id: 'seed-2',
          event_type: 'GREEN_WAVE',
          lat: 26.8563,
          lon: 80.9800,
          timestamp: '2026-10-15T10:05:00.000Z',
          payload: { message: 'Green corridor active on Gomti Nagar IT Arterial. 4 intersections in sync.' },
          severity: 'INFO',
        },
        {
          event_id: 'seed-3',
          event_type: 'SNATCH_ALERT',
          lat: 26.8520,
          lon: 80.9220,
          timestamp: '2026-10-15T10:10:00.000Z',
          payload: { message: 'Kinematic snatch force spike >3.2g logged near Aminabad. UP-112 CAD notified.' },
          severity: 'CRITICAL',
        },
      ];
    }

    if (selectedDepartment) {
      list = list.filter((e) => eventDepartmentMap[e.event_type] === selectedDepartment);
    }

    return list.slice(0, 50);
  }, [events, selectedDepartment]);

  // Auto scroll to bottom when new events arrive
  useEffect(() => {
    if (autoScroll && scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [displayEvents, autoScroll]);

  const getSeverityBadge = (severity: Severity) => {
    switch (severity) {
      case 'CRITICAL':
        return {
          bg: 'bg-rose-500/15',
          text: 'text-rose-300',
          border: 'border-rose-500/50',
          color: '#F43F5E',
        };
      case 'WARNING':
        return {
          bg: 'bg-amber-500/15',
          text: 'text-amber-300',
          border: 'border-amber-500/50',
          color: '#F59E0B',
        };
      case 'INFO':
      default:
        return {
          bg: 'bg-cyan-500/15',
          text: 'text-cyan-300',
          border: 'border-cyan-500/50',
          color: '#06B6D4',
        };
    }
  };

  const getDepartmentLogo = (eventType: string) => {
    const dept = eventDepartmentMap[eventType] || 'MOBILITY';
    switch (dept) {
      case 'SANITATION':
        return <SanitationCoreLogo className="w-4 h-4 flex-shrink-0" />;
      case 'SAFETY':
        return <NirbhayaSafetyLogo className="w-4 h-4 flex-shrink-0" />;
      case 'MOBILITY':
      default:
        return <MobilitySilnLogo className="w-4 h-4 flex-shrink-0" />;
    }
  };

  const formatTime = (isoString: string) => {
    if (!mounted) {
      // Deterministic fallback for server rendering and initial hydration
      try {
        const d = new Date(isoString);
        const h = String(d.getUTCHours()).padStart(2, '0');
        const m = String(d.getUTCMinutes()).padStart(2, '0');
        const s = String(d.getUTCSeconds()).padStart(2, '0');
        return `${h}:${m}:${s}`;
      } catch {
        return '10:00:00';
      }
    }

    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return '--:--:--';
    }
  };

  const getEventDescription = (event: DispatchEvent) => {
    if (event.payload && typeof event.payload === 'object' && 'message' in event.payload) {
      return String(event.payload.message);
    }
    switch (event.event_type) {
      case 'WASTE_OVERFLOW':
        return 'Waste container exceeded critical capacity threshold.';
      case 'SNATCH_ALERT':
        return 'Kinetic snatch/theft velocity spike detected by telemetry.';
      case 'DURESS_TRIGGER':
        return 'Emergency duress code entered or dead-man timer expired.';
      case 'JERK_DETECTED':
        return 'Violent physical acceleration >3.0g logged on citizen sensor.';
      case 'VEHICLE_REROUTE':
        return 'Autonomous corridor recalculation due to bottleneck.';
      case 'GREEN_WAVE':
        return 'Adaptive signal timing progression active.';
      default:
        return 'Telemetry state transition logged.';
    }
  };

  return (
    <div className="bg-[#131d35]/90 backdrop-blur-md border border-slate-700/80 rounded-xl flex flex-col h-[280px] overflow-hidden shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between px-3.5 py-2 border-b border-slate-700/80 bg-slate-900/60">
        <div className="flex items-center gap-2">
          <Radio className="w-4 h-4 text-cyan-400 animate-pulse" />
          <h2 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
            Live Telemetry & Dispatch Feed
          </h2>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-400/40 font-mono font-bold">
            {displayEvents.length} Active
          </span>
        </div>

        <div className="flex items-center gap-2">
          {selectedDepartment && (
            <span className="text-[10px] text-slate-400 font-mono">
              Filtered: <span className="text-cyan-300 font-bold">{selectedDepartment}</span>
            </span>
          )}
          <button
            onClick={() => setAutoScroll((prev) => !prev)}
            title={autoScroll ? 'Pause auto-scroll' : 'Resume auto-scroll'}
            className={`px-2 py-0.5 rounded text-xs transition-all flex items-center gap-1 font-mono font-bold cursor-pointer ${
              autoScroll
                ? 'text-cyan-300 bg-cyan-500/20 border border-cyan-400/50'
                : 'text-slate-400 hover:text-white bg-slate-800'
            }`}
          >
            <ArrowDown className="w-3 h-3" />
            <span className="text-[9px]">{autoScroll ? 'AUTO' : 'PAUSED'}</span>
          </button>
        </div>
      </div>

      {/* Events Scroll Area */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto divide-y divide-slate-800/60 p-2 space-y-1.5"
      >
        {displayEvents.map((evt) => {
          const badge = getSeverityBadge(evt.severity);
          const isCritical = evt.severity === 'CRITICAL';

          return (
            <div
              key={evt.event_id}
              className={`p-2.5 rounded-lg bg-slate-900/60 hover:bg-slate-800/80 transition-all text-xs border ${
                isCritical
                  ? 'border-l-4 border-l-rose-500 border-rose-500/40 bg-rose-500/10 shadow-[0_0_15px_rgba(244,63,94,0.2)]'
                  : 'border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-1">
                <div className="flex items-center gap-2 flex-wrap">
                  {getDepartmentLogo(evt.event_type)}
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded-full border uppercase font-extrabold tracking-wider ${badge.bg} ${badge.text} ${badge.border}`}
                  >
                    {evt.event_type.replace(/_/g, ' ')}
                  </span>

                  <span className="text-[10px] text-slate-400 font-mono" suppressHydrationWarning>
                    {formatTime(evt.timestamp)}
                  </span>
                </div>

                <div className="flex items-center gap-1 text-[10px] text-slate-400 font-mono">
                  <MapPin className="w-2.5 h-2.5 text-cyan-400" />
                  <span>
                    {evt.lat.toFixed(4)}, {evt.lon.toFixed(4)}
                  </span>
                </div>
              </div>

              <p className="text-[11px] text-slate-200 leading-snug pl-6 font-normal">
                {getEventDescription(evt)}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
