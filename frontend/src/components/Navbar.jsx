import React from 'react';
import { Sparkles, Clock, RefreshCw, Shield, Truck, LogOut, User } from 'lucide-react';

export default function Navbar({
  virtualTime,
  activeRole,
  setActiveRole,
  onRefresh,
  loading,
  currentUser,
  onLogout
}) {
  const formattedTime = virtualTime
    ? new Date(virtualTime).toLocaleString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short'
      })
    : 'Initializing Virtual Clock...';

  return (
    <header className="navbar-wrapper">
      {/* Top Row for Brand + User Controls on Mobile */}
      <div className="navbar-top-row">
        {/* Brand & Logo */}
        <div className="navbar-brand-section">
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)',
            flexShrink: 0
          }}>
            <Sparkles size={20} color="#ffffff" />
          </div>
          <div>
            <h1 style={{ fontSize: '16px', fontWeight: '800', margin: 0, color: '#f8fafc', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
              WasteFlow <span style={{ color: '#10b981', fontSize: '10px', fontWeight: '700', padding: '2px 6px', background: 'rgba(16,185,129,0.15)', borderRadius: '6px' }}>AI OPTIMIZER</span>
            </h1>
            <p style={{ fontSize: '11px', color: '#94a3b8', margin: 0 }}>
              Kochi Smart Waste Monitoring
            </p>
          </div>
        </div>

        {/* Right Controls: Sync & Profile */}
        <div className="navbar-actions-section">
          {/* Refresh Data */}
          <button
            onClick={onRefresh}
            disabled={loading}
            className="glass-pill"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '34px',
              height: '34px',
              borderRadius: '9px',
              cursor: loading ? 'not-allowed' : 'pointer',
              color: '#cbd5e1'
            }}
            title="Refresh live data"
          >
            <RefreshCw size={15} className={loading ? 'animate-spin-slow' : ''} />
          </button>

          {/* Logged in User Profile & Logout */}
          {currentUser && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ textAlign: 'right', display: 'none', minWidth: '60px' }} className="user-text-label">
                <div style={{ fontSize: '12px', fontWeight: '700', color: '#f8fafc' }}>
                  {currentUser.name ? currentUser.name.split(' ')[0] : currentUser.username}
                </div>
              </div>

              <button
                onClick={onLogout}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '6px 10px',
                  borderRadius: '8px',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  background: 'rgba(239, 68, 68, 0.1)',
                  color: '#f87171',
                  fontSize: '11px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  transition: 'background 0.2s'
                }}
                title="Log out of session"
              >
                <LogOut size={13} />
                <span className="logout-text">Logout</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Center/Bottom: Virtual Simulation Clock */}
      <div className="navbar-clock-pill">
        <Clock size={14} color="#10b981" className="animate-pulse" style={{ flexShrink: 0 }} />
        <span style={{ fontSize: '11px', fontWeight: '600', color: '#94a3b8' }}>Virtual Sim:</span>
        <span style={{ fontSize: '11.5px', fontWeight: '700', color: '#34d399', fontFamily: 'JetBrains Mono, monospace', whiteSpace: 'nowrap' }}>
          {formattedTime}
        </span>
      </div>
    </header>
  );
}
