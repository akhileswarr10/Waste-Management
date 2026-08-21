import React from 'react';
import { FastForward, Calendar, RotateCcw, Play, Sparkles } from 'lucide-react';

export default function SimulationToolbar({ onAdvanceTime, onResetSimulation, onCollectAll, advancing, resetting, collectingAll }) {
  return (
    <div className="glass-panel sim-toolbar-wrapper">
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: '8px',
          background: 'rgba(96, 165, 250, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0
        }}>
          <Sparkles size={18} color="#60a5fa" />
        </div>
        <div>
          <h4 style={{ fontSize: '13.5px', fontWeight: '700', color: '#f8fafc', margin: 0 }}>
            Time-Step Telemetry Simulation Control
          </h4>
          <p style={{ fontSize: '11.5px', color: 'var(--text-secondary)', margin: 0 }}>
            Simulate realistic IoT stochastic fill rate changes, weekend spikes, and advance clock
          </p>
        </div>
      </div>

      {/* Control Buttons */}
      <div className="sim-buttons-group">
        {/* +6 Hours */}
        <button
          onClick={() => onAdvanceTime(6)}
          disabled={advancing || resetting}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            borderRadius: '10px',
            border: 'none',
            cursor: (advancing || resetting) ? 'not-allowed' : 'pointer',
            background: 'linear-gradient(135deg, #10b981, #059669)',
            color: '#ffffff',
            fontWeight: '700',
            fontSize: '12.5px',
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
            padding: '8px 16px',
            borderRadius: '10px',
            border: 'none',
            cursor: (advancing || resetting) ? 'not-allowed' : 'pointer',
            background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
            color: '#ffffff',
            fontWeight: '700',
            fontSize: '12.5px',
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
          disabled={advancing || resetting || collectingAll}
          className="glass-pill"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 14px',
            borderRadius: '10px',
            cursor: (advancing || resetting || collectingAll) ? 'not-allowed' : 'pointer',
            color: '#ef4444',
            fontWeight: '600',
            fontSize: '12.5px',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            transition: 'background 0.2s',
            opacity: (advancing || resetting || collectingAll) ? 0.7 : 1
          }}
          title="Reset simulation to initial baseline fills"
        >
          <RotateCcw size={15} />
          Reset Baseline
        </button>

        {/* Mark All Route Stops Completed */}
        {onCollectAll && (
          <button
            onClick={onCollectAll}
            disabled={advancing || resetting || collectingAll}
            className="sim-btn-full"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '8px 16px',
              borderRadius: '10px',
              border: 'none',
              cursor: (advancing || resetting || collectingAll) ? 'not-allowed' : 'pointer',
              background: 'linear-gradient(135deg, #059669, #047857)',
              color: '#ffffff',
              fontWeight: '700',
              fontSize: '12.5px',
              boxShadow: '0 4px 14px rgba(16, 185, 129, 0.4)',
              transition: 'transform 0.15s',
              opacity: (advancing || resetting || collectingAll) ? 0.7 : 1
            }}
            title="Collect all routed bins in one click"
          >
            <Sparkles size={16} className={collectingAll ? 'animate-spin-slow' : ''} />
            {collectingAll ? 'Collecting All...' : 'Mark All Route as Completed'}
          </button>
        )}
      </div>
    </div>
  );
}
