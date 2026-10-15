'use client';

import React, { useState, useEffect } from 'react';
import { ShieldCheck, Delete, Check, Lock, AlertOctagon } from 'lucide-react';
import { useUrbanSyncStore } from '@/store/useUrbanSyncStore';
import { useSocket } from '@/hooks/useSocket';

interface DuressModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSafeEnd?: () => void;
}

export default function DuressModal({ isOpen, onClose, onSafeEnd }: DuressModalProps) {
  const [pin, setPin] = useState<string>('');
  const [attemptsRemaining, setAttemptsRemaining] = useState<number>(3);
  const [isShaking, setIsShaking] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const { sendMessage } = useSocket('citizen');
  const triggerDuress = useUrbanSyncStore((s) => s.triggerDuress);
  const endEscort = useUrbanSyncStore((s) => s.endEscort);

  // Reset state when opened
  useEffect(() => {
    if (isOpen) {
      setPin('');
      setAttemptsRemaining(3);
      setIsShaking(false);
      setSuccessMessage(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleDigitClick = (digit: string) => {
    if (pin.length < 4 && !successMessage) {
      setPin((prev) => prev + digit);
    }
  };

  const handleBackspace = () => {
    if (!successMessage) {
      setPin((prev) => prev.slice(0, -1));
    }
  };

  const handleClear = () => {
    if (!successMessage) {
      setPin('');
    }
  };

  const executeSafeCompletion = () => {
    setSuccessMessage('Trip Ended Safely ✓');
    endEscort();
    if (onSafeEnd) onSafeEnd();
    setTimeout(() => {
      onClose();
    }, 1600);
  };

  const executeSilentDuress = () => {
    // Silently notify command center via WebSocket & Store with CODE_RED_P1
    const emergencyPayload = {
      citizen_id: 'citizen-user-01',
      lat: 12.9716,
      lon: 77.5946,
      pin_type: 'DURESS' as const,
      timestamp: new Date().toISOString(),
      code: 'CODE_RED_P1' as const,
    };

    triggerDuress(emergencyPayload);
    sendMessage({
      type: 'SAFETY_ALERT',
      payload: emergencyPayload,
    });

    // To the user/coercer, show the IDENTICAL reassuring confirmation message
    setSuccessMessage('Trip Ended Safely ✓');
    endEscort();
    if (onSafeEnd) onSafeEnd();
    setTimeout(() => {
      onClose();
    }, 1600);
  };

  const handleFailedAttempt = () => {
    const nextAttempts = attemptsRemaining - 1;
    setAttemptsRemaining(nextAttempts);
    setIsShaking(true);
    setTimeout(() => setIsShaking(false), 450);
    setPin('');

    if (nextAttempts <= 0) {
      // Auto-escalate after 3 consecutive failures
      const escalationPayload = {
        citizen_id: 'citizen-user-01',
        lat: 12.9716,
        lon: 77.5946,
        pin_type: 'DURESS' as const,
        timestamp: new Date().toISOString(),
        code: 'CODE_RED_P1' as const,
      };
      triggerDuress(escalationPayload);
      sendMessage({
        type: 'SAFETY_ALERT',
        payload: escalationPayload,
      });

      // Show closed state and exit
      setSuccessMessage('Trip Ended Safely ✓');
      setTimeout(() => {
        onClose();
      }, 1500);
    }
  };

  const handleVerify = () => {
    if (pin.length !== 4) return;

    if (pin === '1234') {
      // Safe PIN
      executeSafeCompletion();
    } else if (pin === '9999') {
      // Silent Duress PIN
      executeSilentDuress();
    } else {
      // Incorrect PIN
      handleFailedAttempt();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in duration-200">
      <div
        className={`w-full max-w-sm bg-gray-900 border border-gray-800 rounded-3xl p-6 shadow-2xl flex flex-col items-center space-y-5 transition-transform ${
          isShaking ? 'animate-shake border-rose-500 shadow-[0_0_25px_rgba(244,63,94,0.4)]' : ''
        }`}
      >
        {/* Header Icon & Title */}
        <div className="flex flex-col items-center text-center space-y-1">
          <div className="w-12 h-12 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mb-1">
            <Lock className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-white tracking-wide">Verify Your Safety</h2>
          <p className="text-xs text-gray-400 max-w-xs">
            Enter your 4-digit security PIN to confirm you are safe and conclude escort monitoring.
          </p>
        </div>

        {/* Success State Overlay if Completed */}
        {successMessage ? (
          <div className="py-8 flex flex-col items-center justify-center space-y-3 animate-in zoom-in-95 duration-200">
            <div className="w-16 h-16 rounded-full bg-emerald-500/20 border-2 border-emerald-500 flex items-center justify-center text-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.5)]">
              <ShieldCheck className="w-8 h-8" />
            </div>
            <p className="text-base font-bold text-emerald-400 font-mono tracking-wide">
              {successMessage}
            </p>
            <span className="text-xs text-gray-400">Escort completed nominal</span>
          </div>
        ) : (
          <>
            {/* PIN Masked Dots Display */}
            <div className="flex items-center justify-center gap-4 py-2">
              {[0, 1, 2, 3].map((idx) => {
                const isFilled = pin.length > idx;
                return (
                  <div
                    key={idx}
                    className={`w-4 h-4 rounded-full transition-all duration-200 border-2 ${
                      isFilled
                        ? 'bg-cyan-400 border-cyan-300 shadow-[0_0_12px_rgba(6,182,212,0.8)] scale-110'
                        : 'bg-gray-800 border-gray-700'
                    }`}
                  />
                );
              })}
            </div>

            {/* Attempts Remaining Notice */}
            {attemptsRemaining < 3 && (
              <p className="text-xs text-rose-400 font-mono font-medium flex items-center gap-1">
                <AlertOctagon className="w-3.5 h-3.5" />
                Invalid PIN. {attemptsRemaining} attempts left.
              </p>
            )}

            {/* Numeric Keypad Grid (3x4) with min 48px tactile buttons */}
            <div className="grid grid-cols-3 gap-3 w-full max-w-[280px]">
              {['1', '2', '3', '4', '5', '6', '7', '8', '9'].map((digit) => (
                <button
                  key={digit}
                  onClick={() => handleDigitClick(digit)}
                  className="h-14 min-h-[48px] rounded-2xl bg-gray-800/80 hover:bg-gray-700 active:bg-cyan-600 active:text-white border border-gray-700/80 text-xl font-bold font-mono text-gray-100 transition-all active:scale-95 flex items-center justify-center cursor-pointer shadow-sm"
                >
                  {digit}
                </button>
              ))}

              {/* Backspace Button */}
              <button
                onClick={handleBackspace}
                className="h-14 min-h-[48px] rounded-2xl bg-gray-800/60 hover:bg-gray-700/80 active:bg-gray-600 border border-gray-700/80 text-gray-400 hover:text-gray-200 transition-all active:scale-95 flex items-center justify-center cursor-pointer"
                title="Delete"
              >
                <Delete className="w-5 h-5" />
              </button>

              {/* Zero Button */}
              <button
                onClick={() => handleDigitClick('0')}
                className="h-14 min-h-[48px] rounded-2xl bg-gray-800/80 hover:bg-gray-700 active:bg-cyan-600 active:text-white border border-gray-700/80 text-xl font-bold font-mono text-gray-100 transition-all active:scale-95 flex items-center justify-center cursor-pointer shadow-sm"
              >
                0
              </button>

              {/* Confirm / Verify Button */}
              <button
                onClick={handleVerify}
                disabled={pin.length !== 4}
                className={`h-14 min-h-[48px] rounded-2xl border transition-all active:scale-95 flex items-center justify-center cursor-pointer font-bold ${
                  pin.length === 4
                    ? 'bg-cyan-500 hover:bg-cyan-400 text-black border-cyan-300 shadow-[0_0_15px_rgba(6,182,212,0.6)]'
                    : 'bg-gray-800/40 text-gray-600 border-gray-800 cursor-not-allowed'
                }`}
                title="Confirm PIN"
              >
                <Check className="w-6 h-6 stroke-[3]" />
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
