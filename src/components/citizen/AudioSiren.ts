/**
 * Emergency dual-oscillator siren synthesizer.
 * Uses Web Audio API to generate an emergency siren without any audio files.
 * 
 * Oscillator 1: Sawtooth wave
 * Oscillator 2: Square wave with +10 cent detune (or ~810Hz base)
 * Frequency ramp: 800Hz → 1200Hz (1s up) then 1200Hz → 800Hz (1s down), repeating
 * Master gain: clamped at 0.15
 */

export class EmergencySiren {
  private audioCtx: AudioContext | null = null;
  private masterGain: GainNode | null = null;
  private osc1: OscillatorNode | null = null;
  private osc2: OscillatorNode | null = null;
  private isPlaying: boolean = false;
  private rampTimer: NodeJS.Timeout | null = null;
  private currentVolume: number = 0.15;

  /**
   * Start dual-oscillator emergency siren with 800Hz-1200Hz frequency modulation.
   */
  public start(): void {
    if (this.isPlaying) return;
    if (typeof window === 'undefined') return;

    try {
      const AudioCtxClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.audioCtx = new AudioCtxClass();

      // Master Gain clamped at 0.15 for ear safety
      this.masterGain = this.audioCtx.createGain();
      this.masterGain.gain.setValueAtTime(this.currentVolume, this.audioCtx.currentTime);
      this.masterGain.connect(this.audioCtx.destination);

      // Oscillator 1: Sawtooth wave at 800Hz
      this.osc1 = this.audioCtx.createOscillator();
      this.osc1.type = 'sawtooth';
      this.osc1.frequency.setValueAtTime(800, this.audioCtx.currentTime);

      // Oscillator 2: Square wave with +10 cent detune
      this.osc2 = this.audioCtx.createOscillator();
      this.osc2.type = 'square';
      this.osc2.frequency.setValueAtTime(800, this.audioCtx.currentTime);
      this.osc2.detune.setValueAtTime(10, this.audioCtx.currentTime);

      this.osc1.connect(this.masterGain);
      this.osc2.connect(this.masterGain);

      this.osc1.start();
      this.osc2.start();
      this.isPlaying = true;

      // Frequency ramp scheduling loop
      this.scheduleRampLoop();
    } catch (err) {
      console.error('[EmergencySiren] Failed to initialize AudioContext:', err);
    }
  }

  private scheduleRampLoop(): void {
    if (!this.isPlaying || !this.audioCtx || !this.osc1 || !this.osc2) return;

    const ctx = this.audioCtx;
    const now = ctx.currentTime;
    const osc1 = this.osc1;
    const osc2 = this.osc2;

    // Ramp 1: 800Hz -> 1200Hz over 1.0 second
    osc1.frequency.setValueAtTime(800, now);
    osc1.frequency.linearRampToValueAtTime(1200, now + 1.0);

    osc2.frequency.setValueAtTime(800, now);
    osc2.frequency.linearRampToValueAtTime(1200, now + 1.0);

    // Ramp 2: 1200Hz -> 800Hz over the next 1.0 second
    osc1.frequency.setValueAtTime(1200, now + 1.0);
    osc1.frequency.linearRampToValueAtTime(800, now + 2.0);

    osc2.frequency.setValueAtTime(1200, now + 1.0);
    osc2.frequency.linearRampToValueAtTime(800, now + 2.0);

    // Schedule next cycle every 2000ms
    this.rampTimer = setTimeout(() => {
      this.scheduleRampLoop();
    }, 2000);
  }

  /**
   * Stop oscillators and release audio context resources.
   */
  public stop(): void {
    if (!this.isPlaying) return;

    if (this.rampTimer) {
      clearTimeout(this.rampTimer);
      this.rampTimer = null;
    }

    try {
      if (this.osc1) {
        this.osc1.stop();
        this.osc1.disconnect();
        this.osc1 = null;
      }
      if (this.osc2) {
        this.osc2.stop();
        this.osc2.disconnect();
        this.osc2 = null;
      }
      if (this.masterGain) {
        this.masterGain.disconnect();
        this.masterGain = null;
      }
      if (this.audioCtx && this.audioCtx.state !== 'closed') {
        this.audioCtx.close();
        this.audioCtx = null;
      }
    } catch (err) {
      console.warn('[EmergencySiren] Error during siren teardown:', err);
    }

    this.isPlaying = false;
  }

  /**
   * Returns true if siren is actively oscillating.
   */
  public isActive(): boolean {
    return this.isPlaying;
  }

  /**
   * Adjust master gain, safely clamped between 0 and 0.15.
   */
  public setVolume(gain: number): void {
    const clamped = Math.max(0, Math.min(0.15, gain));
    this.currentVolume = clamped;
    if (this.masterGain && this.audioCtx) {
      this.masterGain.gain.setValueAtTime(clamped, this.audioCtx.currentTime);
    }
  }
}

// Export singleton instance
export const emergencySiren = new EmergencySiren();
