'use client';

import React, { useEffect, useState, useRef } from 'react';
import { ShieldCheck, XCircle, Heart, AlertTriangle } from 'lucide-react';

interface EscortTimerProps {
  initialSeconds?: number;
  onExpire: () => void;
  onCancel: () => void;
}

export default function EscortTimer({
  initialSeconds = 45,
  onExpire,
  onCancel,
}: EscortTimerProps) {
  const [secondsLeft, setSecondsLeft] = useState<number>(initialSeconds);
  const totalSeconds = initialSeconds;
  const onExpireRef = useRef(onExpire);
  onExpireRef.current = onExpire;

  // Countdown timer effect
  useEffect(() => {
    setSecondsLeft(totalSeconds);

    const interval = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          // Trigger Duress PIN Verification Modal upon reaching 0
          setTimeout(() => {
            onExpireRef.current();
          }, 0);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [totalSeconds]);

  // Color dynamics based on remaining threshold
  let strokeColor = '#10B981'; // Emerald
  let textColor = 'text-emerald-400';
  let badgeColor = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  let isPulsing = false;

  if (secondsLeft <= 15) {
    strokeColor = '#F43F5E'; // Crimson
    textColor = 'text-rose-500';
    badgeColor = 'bg-rose-500/10 text-rose-400 border-rose-500/30';
    isPulsing = true;
  } else if (secondsLeft <= 30) {
    strokeColor = '#F59E0B'; // Amber
    textColor = 'text-amber-400';
    badgeColor = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
  }

  // SVG circle calculations
  const radius = 54;
  const circumference = 2 * Math.PI * radius; // ~339.29
  const strokeDashoffset = circumference - (secondsLeft / totalSeconds) * circumference;

  return (
    <div className="flex flex-col items-center justify-center p-4 bg-gray-900/90 backdrop-blur-md rounded-2xl border border-gray-800 shadow-2xl max-w-sm w-full mx-auto space-y-4">
      {/* Top Banner with Heartbeat Dot */}
      <div className="flex items-center justify-between w-full px-2">
        <div className="flex items-center gap-2">
          <span className="relative flex h-3 w-3">
            <span
              className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
              style={{ backgroundColor: strokeColor }}
            />
            <span
              className="relative inline-flex rounded-full h-3 w-3"
              style={{ backgroundColor: strokeColor }}
            />
          </span>
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-200">
            Dead-Man Heartbeat
          </span>
        </div>

        <div className={`px-2 py-0.5 rounded-full text-[10px] font-mono border ${badgeColor}`}>
          {secondsLeft > 15 ? 'NOMINAL' : 'HEARTBEAT CRITICAL'}
        </div>
      </div>

      {/* Circular SVG Countdown Ring */}
      <div className="relative w-44 h-44 flex items-center justify-center">
        <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 128 128">
          {/* Background Track */}
          <circle
            cx="64"
            cy="64"
            r={radius}
            className="stroke-gray-800"
            strokeWidth="8"
            fill="transparent"
          />
          {/* Animated Progress Ring */}
          <circle
            cx="64"
            cy="64"
            r={radius}
            stroke={strokeColor}
            strokeWidth="8"
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-linear"
            style={{
              filter: `drop-shadow(0 0 8px ${strokeColor}88)`,
            }}
          />
        </svg>

        {/* Inner Content */}
        <div className={`absolute flex flex-col items-center justify-center text-center ${isPulsing ? 'animate-pulse' : ''}`}>
          <Heart className={`w-4 h-4 mb-1 animate-ping ${textColor}`} style={{ animationDuration: `${Math.max(0.6, secondsLeft / 30)}s` }} />
          <span className={`text-4xl font-extrabold font-mono tracking-tighter ${textColor}`}>
            {secondsLeft}s
          </span>
          <span className="text-[10px] text-gray-400 font-mono uppercase tracking-widest mt-0.5">
            Safe Check-In
          </span>
        </div>
      </div>

      {/* Safety Instruction Subtext */}
      <p className="text-xs text-gray-400 text-center px-4 leading-relaxed">
        Autonomous telemetry is monitoring kinetic stability and surveillance corridor alignment. Confirm status before countdown lapses.
      </p>

      {/* Action Buttons */}
      <div className="w-full flex items-center gap-2 pt-1">
        <button
          onClick={onCancel}
          className="flex-1 py-2.5 px-3 rounded-xl bg-gray-800 hover:bg-gray-700/80 text-gray-300 text-xs font-semibold flex items-center justify-center gap-1.5 transition-all border border-gray-700 active:scale-98 cursor-pointer"
        >
          <XCircle className="w-4 h-4 text-gray-400" />
          <span>Cancel Escort</span>
        </button>

        <button
          onClick={() => setSecondsLeft(totalSeconds)}
          className="flex-1 py-2.5 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center justify-center gap-1.5 transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)] active:scale-98 cursor-pointer"
        >
          <ShieldCheck className="w-4 h-4" />
          <span>I am Safe (Reset)</span>
        </button>
      </div>
    </div>
  );
}
