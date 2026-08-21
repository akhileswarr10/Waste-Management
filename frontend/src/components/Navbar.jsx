import React from 'react';
import { Sparkles, Clock, RefreshCw, LogOut } from 'lucide-react';

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

      {/* LEFT: Brand & Logo */}
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
          <h1 style={{ fontSize: '17px', fontWeight: '800', margin: 0, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            WasteFlow{' '}
            <span style={{
              color: '#10b981',
              fontSize: '11px',
              fontWeight: '700',
              padding: '2px 6px',
              background: 'rgba(16,185,129,0.15)',
              borderRadius: '6px',
              marginLeft: '4px'
            }}>AI OPTIMIZER</span>
          </h1>
          <p style={{ fontSize: '11px', color: '#94a3b8', margin: 0 }}>
            Kochi Smart Urban Solid Waste Monitoring
          </p>
        </div>
      </div>

      {/* CENTER: Virtual Simulation Clock */}
      <div className="navbar-clock-pill">
        <Clock size={15} color="#10b981" style={{ flexShrink: 0 }} />
        <span style={{ fontSize: '11px', fontWeight: '600', color: '#94a3b8', whiteSpace: 'nowrap' }}>
          Virtual Sim Time:
        </span>
        <span style={{
          fontSize: '12px',
          fontWeight: '700',
          color: '#34d399',
          fontFamily: 'JetBrains Mono, monospace',
          whiteSpace: 'nowrap'
        }}>
          {formattedTime}
        </span>
      </div>

      {/* RIGHT: Refresh + User Profile + Logout */}
      <div className="navbar-actions-section">
        {/* Refresh */}
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
            color: '#cbd5e1',
            flexShrink: 0
          }}
          title="Refresh live data"
        >
          <RefreshCw size={15} className={loading ? 'animate-spin-slow' : ''} />
        </button>

        {/* User info + Logout */}
        {currentUser && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            paddingLeft: '8px',
            borderLeft: '1px solid rgba(255,255,255,0.1)'
          }}>
            <div className="navbar-user-label">
              <div style={{ fontSize: '12px', fontWeight: '700', color: '#f8fafc' }}>
                {currentUser.name || currentUser.username}
              </div>
              <div style={{
                fontSize: '10px',
                color: currentUser.role === 'admin' ? '#10b981' : '#818cf8',
                fontWeight: '600'
              }}>
                {currentUser.badge || (currentUser.role === 'admin' ? 'Administrator' : 'Fleet Driver')}
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
                transition: 'background 0.2s',
                flexShrink: 0
              }}
              title="Log out of session"
            >
              <LogOut size={13} />
              <span className="logout-text">Logout</span>
            </button>
          </div>
        )}
      </div>

    </header>
  );
}
