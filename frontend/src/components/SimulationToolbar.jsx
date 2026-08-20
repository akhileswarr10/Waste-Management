import React from 'react';
import { FastForward, Calendar, RotateCcw, Play, Sparkles } from 'lucide-react';

export default function SimulationToolbar({ onAdvanceTime, onResetSimulation, advancing, resetting }) {
  return (
    <div className="glass-panel" style={{
      margin: '0 16px 16px 16px',
      padding: '14px 20px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      flexWrap: 'wrap',
      gap: '16px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: '8px',
          background: 'rgba(96, 165, 250, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Sparkles size={18} color="#60a5fa" />
        </div>
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#f8fafc' }}>
            Time-Step Telemetry Simulation Control
          </h4>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Simulate realistic IoT stochastic fill rate changes, weekend spikes, and advance clock
          </p>
        </div>
      </div>

      {/* Control Buttons */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* +6 Hours */}
        <button
          onClick={() => onAdvanceTime(6)}
          disabled={advancing || resetting}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 18px',
            borderRadius: '10px',
            border: 'none',
            cursor: (advancing || resetting) ? 'not-allowed' : 'pointer',
            background: 'linear-gradient(135deg, #10b981, #059669)',
            color: '#ffffff',
            fontWeight: '700',
            fontSize: '13px',
            boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)',
            transition: 'transform 0.15s, filter 0.15s',
            opacity: (advancing || resetting) ? 0.7 : 1
          }}
        >
          <FastForward size={16} className={advancing ? 'animate-spin-slow' : ''} />
          {advancing ? 'Simulating +6h...' : '+6 Hours'}
        </button>

        {/* +1 Day */}
        <button
          onClick={() => onAdvanceTime(24)}
          disabled={advancing || resetting}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 18px',
            borderRadius: '10px',
            border: 'none',
            cursor: (advancing || resetting) ? 'not-allowed' : 'pointer',
            background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
            color: '#ffffff',
            fontWeight: '700',
            fontSize: '13px',
            boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
            transition: 'transform 0.15s, filter 0.15s',
            opacity: (advancing || resetting) ? 0.7 : 1
          }}
        >
          <Calendar size={16} />
          +1 Day (24h)
        </button>

        {/* Reset */}
        <button
          onClick={onResetSimulation}
          disabled={advancing || resetting}
          className="glass-pill"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 14px',
            borderRadius: '10px',
            cursor: (advancing || resetting) ? 'not-allowed' : 'pointer',
            color: '#ef4444',
            fontWeight: '600',
            fontSize: '13px',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            transition: 'background 0.2s',
            opacity: (advancing || resetting) ? 0.7 : 1
          }}
          title="Reset simulation to initial baseline fills"
        >
          <RotateCcw size={15} />
          Reset Baseline
        </button>
      </div>
    </div>
  );
}
