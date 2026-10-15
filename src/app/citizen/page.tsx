'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useSocket } from '../../hooks/useSocket';
import { useUrbanSyncStore } from '../../store/useUrbanSyncStore';
import EscortTimer from '../../components/citizen/EscortTimer';
import DuressModal from '../../components/citizen/DuressModal';
import SafePathMap from '../../components/citizen/SafePathMap';
import { emergencySiren } from '../../components/citizen/AudioSiren';
import type { SurveillanceStatus, EscortSession } from '../../types';
import {
  Shield,
  ShieldAlert,
  AlertTriangle,
  ArrowLeft,
  Volume2,
  CheckCircle,
} from 'lucide-react';
import { NirbhayaSafetyLogo, UP112CadLogo } from '../../components/ui/Logos';

export default function CitizenPage() {
  const { isConnected, sendMessage } = useSocket('citizen');

  const activeEscort = useUrbanSyncStore((s) => s.activeEscort);
  const startEscort = useUrbanSyncStore((s) => s.startEscort);
  const endEscort = useUrbanSyncStore((s) => s.endEscort);
  const surveillanceStatus = useUrbanSyncStore((s) => s.surveillanceStatus);
  const triggerDuress = useUrbanSyncStore((s) => s.triggerDuress);
  const duressTriggered = useUrbanSyncStore((s) => s.duressTriggered);

  const [isDuressModalOpen, setIsDuressModalOpen] = useState<boolean>(false);
  const [isSirenActive, setIsSirenActive] = useState<boolean>(false);
  const [sosFired, setSosFired] = useState<boolean>(false);

  // Sync active escort session with local or store
  const isEscortActive = Boolean(activeEscort?.is_active);

  // Handle start escort
  const handleStartEscort = () => {
    const newSession: EscortSession = {
      citizen_id: 'citizen-user-01',
      started_at: new Date().toISOString(),
      last_heartbeat: new Date().toISOString(),
      is_active: true,
      jerk_detected: false,
      countdown_remaining_sec: 45,
      origin: { lat: 26.8467, lon: 80.9462 },
      destination: { lat: 26.8563, lon: 80.9800 },
    };

    startEscort(newSession);

    // Broadcast session activation to gateway
    sendMessage({
      type: 'TELEMETRY_UPDATE',
      payload: {
        citizen_id: 'citizen-user-01',
        lat: 26.8467,
        lon: 80.9462,
        accel_g: 1.0,
        timestamp: new Date().toISOString(),
        escort_active: true,
        heading_deg: 42.0,
      },
    });
  };

  const handleEndEscort = () => {
    endEscort();
    if (emergencySiren.isActive()) {
      emergencySiren.stop();
      setIsSirenActive(false);
    }
  };

  // Immediate Emergency SOS Button Trigger
  const handleEmergencySOS = useCallback(() => {
    setSosFired(true);

    // Synthesize dual-oscillator siren
    emergencySiren.start();
    setIsSirenActive(true);

    const emergencyPayload = {
      citizen_id: 'citizen-user-01',
      lat: 26.8467,
      lon: 80.9462,
      pin_type: 'DURESS' as const,
      timestamp: new Date().toISOString(),
      code: 'CODE_RED_P1' as const,
    };

    triggerDuress(emergencyPayload);

    sendMessage({
      type: 'SAFETY_ALERT',
      payload: emergencyPayload,
    });

    // Also pop open Duress verification modal so citizen can dismiss or verify
    setIsDuressModalOpen(true);
  }, [triggerDuress, sendMessage]);

  const toggleSirenAudio = () => {
    if (isSirenActive) {
      emergencySiren.stop();
      setIsSirenActive(false);
    } else {
      emergencySiren.start();
      setIsSirenActive(true);
    }
  };

  // Status banner display
  const isLocked = surveillanceStatus === 'SURVEILLANCE_LOCKED';

  return (
    <div
      className={`min-h-screen bg-gradient-to-b from-[#0b1329] via-[#0e1935] to-[#080d1a] text-slate-100 flex flex-col justify-between selection:bg-rose-500/20 ${
        sosFired || duressTriggered ? 'animate-pulse-glow' : ''
      }`}
    >
      {/* Top Header / Status Banner with Official Logos */}
      <header className="sticky top-0 z-40 bg-[#0d162e]/95 backdrop-blur-md border-b border-slate-700/80 shadow-md">
        <div className="max-w-xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white transition-colors bg-slate-800/80 border border-slate-700 px-2.5 py-1 rounded-lg"
          >
            <ArrowLeft className="w-4 h-4 text-cyan-400" />
            <span className="font-mono font-bold">Cockpit</span>
          </Link>

          <div className="flex items-center gap-2">
            <NirbhayaSafetyLogo className="w-6 h-6" />
            <div className="flex flex-col">
              <span className="text-xs font-black uppercase tracking-wider text-white">
                Nirbhaya-Mesh v3.7
              </span>
              <span className="text-[9px] text-pink-400 font-mono font-semibold">
                SafePath AI Guardian
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <UP112CadLogo className="w-6 h-6" />

            {isSirenActive && (
              <button
                onClick={toggleSirenAudio}
                className="p-1.5 rounded-lg bg-rose-500/20 text-rose-300 border border-rose-500/50 hover:bg-rose-500/30 transition-all cursor-pointer"
                title="Toggle Siren Mute"
              >
                <Volume2 className="w-4 h-4 animate-bounce" />
              </button>
            )}

            <div
              className={`flex items-center gap-1.5 text-[10px] font-mono font-bold px-2.5 py-1 rounded-full border ${
                isConnected
                  ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40 shadow-sm'
                  : 'bg-rose-500/15 text-rose-300 border-rose-500/40 shadow-sm'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
                }`}
              />
              <span>{isConnected ? 'CAD SYNC' : 'OFFLINE'}</span>
            </div>
          </div>
        </div>

        {/* Dynamic Safety Status Banner */}
        <div
          className={`w-full py-2 px-4 border-t flex items-center justify-center gap-2 text-xs font-mono font-bold uppercase tracking-wider transition-colors duration-300 ${
            isLocked
              ? 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.25)]'
              : 'bg-rose-950/90 text-rose-300 border-rose-500/50 shadow-[0_0_20px_rgba(244,63,94,0.35)] animate-pulse'
          }`}
        >
          {isLocked ? (
            <>
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              <span>SURVEILLANCE_LOCKED: High CCTV Cones & UP-112 Patrol Intersect</span>
            </>
          ) : (
            <>
              <AlertTriangle className="w-4 h-4 text-rose-400 animate-bounce" />
              <span>BLIND_SPOT_DETECTED: Active Camera Deviation — SafePath Routing Active</span>
            </>
          )}
        </div>
      </header>

      {/* Main Content Area (Max Mobile Width) */}
      <main className="flex-1 max-w-xl w-full mx-auto p-4 space-y-4">
        {/* SafePath Map & Route Comparison Section */}
        <SafePathMap />

        {/* Active Escort Mode Card or Status Overview */}
        {isEscortActive && (
          <div className="pt-2 animate-in fade-in duration-300">
            <EscortTimer
              initialSeconds={45}
              onExpire={() => setIsDuressModalOpen(true)}
              onCancel={handleEndEscort}
            />
          </div>
        )}
      </main>

      {/* Bottom Sticky Action Footer */}
      <footer className="sticky bottom-0 z-40 bg-[#0d162e]/95 backdrop-blur-lg border-t border-slate-700/80 p-4 shadow-lg">
        <div className="max-w-xl mx-auto space-y-3">
          {/* Main Action: Start Escort OR Escort Active State */}
          {!isEscortActive ? (
            <button
              onClick={handleStartEscort}
              className="w-full py-4 px-6 rounded-2xl bg-gradient-to-r from-emerald-600 via-emerald-500 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-bold text-base shadow-[0_4px_25px_rgba(16,185,129,0.4)] active:scale-98 transition-all flex items-center justify-center gap-3 cursor-pointer border border-emerald-300/40"
            >
              <div className="p-1.5 rounded-xl bg-black/25">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div className="flex flex-col text-left">
                <span className="leading-tight text-sm font-extrabold tracking-wide uppercase">
                  Start Dead-Man Escort
                </span>
                <span className="text-[10px] text-emerald-100 font-normal opacity-90">
                  45s Heartbeat Auto-Checkin • Kinetic Jerk Sensor Active
                </span>
              </div>
            </button>
          ) : (
            <div className="flex items-center justify-between bg-emerald-950/70 border border-emerald-500/50 p-3 rounded-xl text-xs font-mono text-emerald-300 shadow-sm">
              <div className="flex items-center gap-2 font-bold">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                <span>ESCORT RUNNING: Telemetry Live</span>
              </div>
              <button
                onClick={() => setIsDuressModalOpen(true)}
                className="px-3 py-1.5 rounded-lg bg-emerald-500/30 border border-emerald-400 text-emerald-200 hover:bg-emerald-500/40 transition-all font-bold cursor-pointer"
              >
                Safe Check-In
              </button>
            </div>
          )}

          {/* Emergency SOS Button (Pulsing Crimson) */}
          <button
            onClick={handleEmergencySOS}
            className="w-full py-3.5 px-6 rounded-2xl bg-gradient-to-r from-rose-700 via-rose-600 to-red-600 hover:from-rose-600 hover:to-red-500 text-white font-extrabold text-sm shadow-[0_0_30px_rgba(244,63,94,0.6)] active:scale-98 transition-all flex items-center justify-center gap-2 border border-rose-300/50 cursor-pointer animate-siren-flash uppercase tracking-wider"
          >
            <ShieldAlert className="w-5 h-5 animate-spin" style={{ animationDuration: '3s' }} />
            <span>Emergency SOS (Silent UP-112 CAD Trigger)</span>
          </button>
        </div>
      </footer>

      {/* Duress Verification Keypad Modal */}
      <DuressModal
        isOpen={isDuressModalOpen}
        onClose={() => setIsDuressModalOpen(false)}
        onSafeEnd={() => {
          if (emergencySiren.isActive()) {
            emergencySiren.stop();
            setIsSirenActive(false);
          }
        }}
      />
    </div>
  );
}
