'use client';

import React from 'react';
import { useUrbanSyncStore } from '@/store/useUrbanSyncStore';
import { Clock, Layers, Sparkles } from 'lucide-react';
import { SanitationCoreLogo } from '../ui/Logos';

export default function TimeSlider() {
  const timeSliderValue = useUrbanSyncStore((s) => s.timeSliderValue);
  const setTimeSlider = useUrbanSyncStore((s) => s.setTimeSlider);

  const steps = [
    {
      id: 0,
      code: 'T0',
      label: 'Baseline Clean',
      timestamp: '08:00 AM',
      description: 'Pre-shift municipal street scan baseline (ORB Homography)',
      accent: 'text-slate-300',
    },
    {
      id: 1,
      code: 'T1',
      label: 'Midday Accumulation',
      timestamp: '01:30 PM',
      description: 'Temporal debris delta detection & volumetric mask integration',
      accent: 'text-amber-300',
    },
    {
      id: 2,
      code: 'T2',
      label: 'Active CVRP Clearance',
      timestamp: '05:45 PM',
      description: 'Google OR-Tools autonomous fleet rerouting and container flush',
      accent: 'text-cyan-300',
    },
  ];

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    setTimeSlider(val);
  };

  return (
    <div className="bg-[#131d35]/90 backdrop-blur-md border border-slate-700/80 rounded-xl p-3.5 space-y-3 shadow-lg">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <SanitationCoreLogo className="w-4 h-4 text-cyan-400" />
          <h2 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
            Temporal Scrubber — Debris Delta ($T_0 \to T_1 \to T_2$)
          </h2>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] font-mono text-cyan-300 bg-cyan-950/80 px-2.5 py-0.5 rounded-full border border-cyan-400/50 shadow-sm font-bold">
          <Clock className="w-3 h-3 text-cyan-400" />
          <span>Active: {steps[timeSliderValue]?.code} ({steps[timeSliderValue]?.timestamp})</span>
        </div>
      </div>

      {/* Visual Timeline Bar & Input */}
      <div className="relative pt-2 pb-1">
        {/* Custom Track Background with Gradient */}
        <div className="h-2.5 rounded-full w-full bg-slate-900 relative overflow-hidden border border-slate-700 shadow-inner">
          <div
            className="h-full bg-gradient-to-r from-cyan-500 via-sky-400 to-emerald-400 transition-all duration-300 rounded-full shadow-[0_0_15px_rgba(6,182,212,0.8)]"
            style={{ width: `${(timeSliderValue / 2) * 100}%` }}
          />
        </div>

        {/* Range Input element overlaid transparently */}
        <input
          type="range"
          min={0}
          max={2}
          step={1}
          value={timeSliderValue}
          onChange={handleSliderChange}
          aria-label="Temporal time slider"
          className="absolute inset-x-0 top-1 w-full h-5 opacity-0 cursor-pointer z-20"
        />

        {/* Step Nodes Indicators */}
        <div className="flex justify-between items-center relative -mt-4 z-10 pointer-events-none px-0.5">
          {steps.map((step) => {
            const isActive = timeSliderValue === step.id;
            const isPassed = timeSliderValue >= step.id;

            return (
              <div key={step.id} className="flex flex-col items-center">
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center border-2 transition-all duration-300 pointer-events-auto cursor-pointer ${
                    isActive
                      ? 'bg-cyan-400 border-white shadow-[0_0_16px_rgba(6,182,212,1)] scale-125'
                      : isPassed
                      ? 'bg-slate-900 border-cyan-400 text-cyan-300'
                      : 'bg-slate-900 border-slate-600 text-slate-500'
                  }`}
                  onClick={() => setTimeSlider(step.id)}
                >
                  <span className={`text-[9px] font-mono font-black ${isActive ? 'text-slate-950' : 'text-white'}`}>
                    {step.code.charAt(1)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Step Labels & Information Card */}
      <div className="grid grid-cols-3 gap-2 pt-1 text-center">
        {steps.map((step) => {
          const isActive = timeSliderValue === step.id;

          return (
            <button
              key={step.id}
              onClick={() => setTimeSlider(step.id)}
              className={`p-2 rounded-xl text-left transition-all cursor-pointer border ${
                isActive
                  ? 'bg-cyan-500/15 border-cyan-400 text-white shadow-[0_0_15px_rgba(6,182,212,0.3)]'
                  : 'bg-slate-900/60 border-slate-700/70 hover:bg-slate-800/80 text-slate-400'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className={`text-[11px] font-mono font-extrabold ${isActive ? 'text-cyan-300' : 'text-slate-400'}`}>
                  {step.code}
                </span>
                <span className="text-[9px] text-slate-400 font-mono">{step.timestamp}</span>
              </div>
              <p className={`text-[11px] font-bold truncate mt-0.5 ${isActive ? 'text-white' : 'text-slate-300'}`}>
                {step.label}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
