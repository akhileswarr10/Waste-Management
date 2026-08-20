import React from 'react';
import { Activity, Clock, Shield, Truck, RefreshCw, Zap, MapPin } from 'lucide-react';

export default function Navbar({
  virtualTime,
  activeRole,
  setActiveRole,
  activeView,
  setActiveView,
  onRefresh,
  loading
}) {
  const formatVirtualTime = (isoStr) => {
    if (!isoStr) return 'Syncing...';
    try {
      const dt = new Date(isoStr);
      return dt.toUTCString().replace('GMT', 'UTC');
    } catch {
      return isoStr;
    }
  };

  return (
    <header className="glass-panel" style={{ margin: '16px', padding: '14px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '42px',
          height: '42px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, #10b981, #047857)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 15px rgba(16, 185, 129, 0.4)'
        }}>
          <Zap size={24} color="#ffffff" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h1 style={{ fontSize: '20px', fontWeight: '800', letterSpacing: '-0.5px', background: 'linear-gradient(90deg, #34d399, #60a5fa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              WasteFlow
            </h1>
            <span className="glass-pill" style={{ padding: '2px 8px', borderRadius: '20px', fontSize: '11px', fontWeight: '600', color: '#10b981' }}>
              ML v2.0
            </span>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Smart Predictive Waste Routing & Corridor Optimization
          </p>
        </div>
      </div>

      {/* Virtual Clock Display */}
      <div className="glass-pill" style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 16px', borderRadius: '12px' }}>
        <Clock size={16} color="#60a5fa" />
        <div>
          <span style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.5px', color: '#94a3b8', display: 'block', fontWeight: '600' }}>
            Virtual Simulation Clock
          </span>
          <span style={{ fontSize: '13px', fontWeight: '600', color: '#f8fafc', fontFamily: 'monospace' }}>
            {formatVirtualTime(virtualTime)}
          </span>
        </div>
      </div>

      {/* Navigation View & Role Selector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Role Switcher */}
        <div className="glass-pill" style={{ display: 'flex', padding: '4px', borderRadius: '12px', gap: '4px' }}>
          <button
            onClick={() => { setActiveRole('admin'); setActiveView('admin'); }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '13px',
              background: activeRole === 'admin' ? 'linear-gradient(135deg, #10b981, #059669)' : 'transparent',
              color: activeRole === 'admin' ? '#ffffff' : '#94a3b8',
              transition: 'all 0.2s'
            }}
          >
            <Shield size={15} />
            Admin Hub
          </button>

          <button
            onClick={() => { setActiveRole('driver'); setActiveView('driver'); }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '13px',
              background: activeRole === 'driver' ? 'linear-gradient(135deg, #6366f1, #4f46e5)' : 'transparent',
              color: activeRole === 'driver' ? '#ffffff' : '#94a3b8',
              transition: 'all 0.2s'
            }}
          >
            <Truck size={15} />
            Driver Route View
          </button>
        </div>

        {/* Global Refresh */}
        <button
          onClick={onRefresh}
          disabled={loading}
          className="glass-pill"
          style={{
            padding: '8px 12px',
            borderRadius: '10px',
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            color: '#94a3b8',
            fontSize: '13px',
            fontWeight: '500'
          }}
          title="Refresh live telemetry & predictions"
        >
          <RefreshCw size={15} className={loading ? 'animate-spin-slow' : ''} />
          <span>Sync</span>
        </button>
      </div>
    </header>
  );
}
