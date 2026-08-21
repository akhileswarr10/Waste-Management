import React from 'react';
import { Navigation, CheckCircle2, Fuel, Clock, MapPin, Sparkles, AlertCircle } from 'lucide-react';

export default function RoutePanel({
  routeData,
  onCollectBin,
  onCollectAll,
  collectingBinId,
  collectingAll,
  isDriverView = false
}) {
  const summary = routeData?.summary || {};
  const stops = routeData?.stops || [];
  const pendingCollectionCount = stops.filter(s => !s.is_depot && s.bin_id).length;

  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Navigation size={18} color="#818cf8" />
            <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#f8fafc' }}>
              {isDriverView ? 'Driver Assigned Route Manifest' : 'Greedy Route & Corridor Pipeline'}
            </h3>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Optimized sequence prioritizing critical bins with on-the-way corridor collections
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {onCollectAll && pendingCollectionCount > 0 && (
            <button
              onClick={onCollectAll}
              disabled={collectingAll}
              style={{
                padding: '6px 14px',
                borderRadius: '8px',
                border: 'none',
                cursor: collectingAll ? 'not-allowed' : 'pointer',
                background: 'linear-gradient(135deg, #10b981, #059669)',
                color: '#ffffff',
                fontWeight: '700',
                fontSize: '12px',
                boxShadow: '0 4px 12px rgba(16, 185, 129, 0.35)',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                opacity: collectingAll ? 0.7 : 1
              }}
            >
              <CheckCircle2 size={15} className={collectingAll ? 'animate-spin-slow' : ''} />
              {collectingAll ? 'Collecting All...' : `Mark All as Completed (${pendingCollectionCount})`}
            </button>
          )}

          <span className="glass-pill" style={{ padding: '4px 10px', borderRadius: '8px', fontSize: '11px', fontWeight: '700', color: '#818cf8', border: '1px solid rgba(129, 140, 248, 0.3)' }}>
            {summary.total_collection_stops || 0} Total Stops
          </span>
        </div>
      </div>

      {/* Metrics Banner */}
      <div className="route-metrics-grid">
        <div>
          <span style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase' }}>Route Distance</span>
          <div style={{ fontSize: '16px', fontWeight: '800', color: '#f8fafc' }}>
            {summary.total_route_distance_km || 0} km
          </div>
          <span style={{ fontSize: '10px', color: '#10b981' }}>
            -{summary.distance_saved_km || 0} km saved
          </span>
        </div>

        <div>
          <span style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase' }}>Est. Total Time</span>
          <div style={{ fontSize: '16px', fontWeight: '800', color: '#60a5fa' }}>
            {summary.estimated_duration_minutes || 0} min
          </div>
          <span style={{ fontSize: '10px', color: '#94a3b8' }}>
            Drive + Ops
          </span>
        </div>

        <div>
          <span style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase' }}>Fuel Savings</span>
          <div style={{ fontSize: '16px', fontWeight: '800', color: '#34d399' }}>
            {summary.fuel_savings_pct || 0}%
          </div>
          <span style={{ fontSize: '10px', color: '#34d399' }}>
            ₹{summary.estimated_cost_savings_inr || 0}
          </span>
        </div>
      </div>

      {/* Sequential Stops Checklist */}
      <div style={{ overflowY: 'auto', flex: 1, maxHeight: '380px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {stops.map((s, idx) => {
          const isDepot = s.type.includes('depot');
          const isOtw = s.is_on_the_way;
          const isCollecting = collectingBinId === s.bin_id;

          return (
            <div
              key={idx}
              style={{
                padding: '12px 14px',
                borderRadius: '12px',
                background: isDepot ? 'rgba(99, 102, 241, 0.1)' : isOtw ? 'rgba(245, 158, 11, 0.08)' : 'rgba(255, 255, 255, 0.04)',
                border: isDepot ? '1px solid rgba(99, 102, 241, 0.25)' : isOtw ? '1px solid rgba(245, 158, 11, 0.2)' : '1px solid rgba(255, 255, 255, 0.06)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '12px'
              }}
            >
              {/* Stop info */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  background: isDepot ? '#6366f1' : isOtw ? '#f59e0b' : '#ef4444',
                  color: '#ffffff',
                  fontWeight: '800',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  {isDepot ? (idx === 0 ? 'S' : 'E') : s.stop_number}
                </div>

                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontWeight: '700', fontSize: '13px', color: '#f8fafc' }}>
                      {isDepot ? s.name : `Bin ${s.bin_id}`}
                    </span>
                    {isOtw && (
                      <span className="glass-pill" style={{ fontSize: '9px', fontWeight: '700', padding: '1px 5px', borderRadius: '4px', color: '#fbbf24', border: '1px solid rgba(251, 191, 36, 0.3)' }}>
                        ON-THE-WAY
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                    {isDepot ? 'Vehicle Dispatch Base' : `${s.area_type} (${s.locality}) • ${s.current_fill_level_pct}% Fill`}
                  </div>
                </div>
              </div>

              {/* Action / ETA */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontSize: '12px', fontWeight: '700', color: '#60a5fa', display: 'block' }}>
                    +{s.eta_minutes}m
                  </span>
                  <span style={{ fontSize: '10px', color: '#94a3b8' }}>
                    {s.distance_from_prev_km} km
                  </span>
                </div>

                {!isDepot && onCollectBin && (
                  <button
                    onClick={() => onCollectBin(s.bin_id)}
                    disabled={isCollecting}
                    style={{
                      padding: '6px 12px',
                      borderRadius: '8px',
                      border: 'none',
                      cursor: isCollecting ? 'not-allowed' : 'pointer',
                      background: 'linear-gradient(135deg, #10b981, #059669)',
                      color: '#ffffff',
                      fontWeight: '700',
                      fontSize: '11px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      boxShadow: '0 2px 8px rgba(16, 185, 129, 0.3)',
                      opacity: isCollecting ? 0.7 : 1
                    }}
                  >
                    <CheckCircle2 size={13} />
                    {isCollecting ? 'Emptying...' : 'Mark Collected'}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
