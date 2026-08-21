import React, { useState } from 'react';
import { Search, Filter, AlertCircle, ArrowUpDown } from 'lucide-react';

export default function BinsTable({ bins = [], onSelectBin = null }) {
  const [search, setSearch] = useState('');
  const [selectedTier, setSelectedTier] = useState('ALL');

  const filteredBins = bins.filter(b => {
    const matchesSearch = b.bin_id.toLowerCase().includes(search.toLowerCase()) ||
                          b.area_type.toLowerCase().includes(search.toLowerCase()) ||
                          b.locality.toLowerCase().includes(search.toLowerCase()) ||
                          b.collection_zone.toLowerCase().includes(search.toLowerCase());
    const matchesTier = selectedTier === 'ALL' || b.urgency_tier === selectedTier;
    return matchesSearch && matchesTier;
  });

  return (
    <div className="glass-panel" style={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#f8fafc' }}>
            Live Smart Bin Telemetry & Predictions
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Showing {filteredBins.length} of {bins.length} monitored waste containers
          </p>
        </div>

        {/* Search & Filter Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', width: '100%', maxWidth: '400px' }}>
          <div className="glass-pill" style={{ display: 'flex', alignItems: 'center', padding: '6px 12px', borderRadius: '10px', gap: '8px', flex: 1, minWidth: '140px' }}>
            <Search size={14} color="#94a3b8" />
            <input
              type="text"
              placeholder="Search Bin, Zone, Area..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ background: 'transparent', border: 'none', color: '#f8fafc', fontSize: '12px', outline: 'none', width: '100%' }}
            />
          </div>

          <select
            value={selectedTier}
            onChange={(e) => setSelectedTier(e.target.value)}
            className="glass-pill"
            style={{
              padding: '6px 12px',
              borderRadius: '10px',
              color: '#f8fafc',
              background: 'rgba(15, 23, 42, 0.8)',
              fontSize: '12px',
              outline: 'none',
              cursor: 'pointer'
            }}
          >
            <option value="ALL">All Tiers</option>
            <option value="EMERGENCY">Emergency (100%)</option>
            <option value="CRITICAL">Critical (≥90%)</option>
            <option value="HIGH">High (75-89%)</option>
            <option value="MEDIUM">Medium (50-74%)</option>
            <option value="LOW">Low (&lt;50%)</option>
          </select>
        </div>
      </div>

      {/* Table Content */}
      <div className="table-responsive-wrapper" style={{ overflowX: 'auto', flex: 1, maxHeight: '420px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#94a3b8' }}>
              <th style={{ padding: '10px 12px', fontWeight: '600' }}>BIN ID</th>
              <th style={{ padding: '10px 12px', fontWeight: '600' }}>ZONE / LOCALITY</th>
              <th style={{ padding: '10px 12px', fontWeight: '600' }}>AREA TYPE</th>
              <th style={{ padding: '10px 12px', fontWeight: '600' }}>CURRENT FILL</th>
              <th style={{ padding: '10px 12px', fontWeight: '600' }}>6H FORECAST</th>
              <th style={{ padding: '10px 12px', fontWeight: '600' }}>PRIORITY</th>
              <th style={{ padding: '10px 12px', fontWeight: '600' }}>STATUS</th>
              <th style={{ padding: '10px 12px', fontWeight: '600' }}>ACTION</th>
            </tr>
          </thead>
          <tbody>
            {filteredBins.map((b) => {
              const tier = b.urgency_tier || 'LOW';
              const fill = b.current_fill_level_pct || 0;
              const pred = b.predicted_fill_6h_pct || fill;

              return (
                <tr
                  key={b.bin_id}
                  onClick={() => onSelectBin && onSelectBin(b)}
                  style={{
                    borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                    cursor: onSelectBin ? 'pointer' : 'default',
                    transition: 'background 0.15s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <td style={{ padding: '12px', fontWeight: '700', color: '#f8fafc', fontFamily: 'monospace' }}>
                    {b.bin_id}
                  </td>
                  <td style={{ padding: '12px', color: '#cbd5e1' }}>
                    {b.collection_zone} ({b.locality})
                  </td>
                  <td style={{ padding: '12px', color: '#cbd5e1' }}>
                    {b.area_type}
                  </td>
                  <td style={{ padding: '12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ width: '50px', height: '6px', borderRadius: '3px', background: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
                        <div style={{
                          height: '100%',
                          width: `${Math.min(100, fill)}%`,
                          background: fill >= 90 ? '#ef4444' : fill >= 75 ? '#f97316' : fill >= 50 ? '#f59e0b' : '#10b981'
                        }} />
                      </div>
                      <span style={{ fontWeight: '700', color: fill >= 80 ? '#f87171' : '#f8fafc' }}>
                        {fill}%
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '12px', fontWeight: '600', color: pred >= 90 ? '#f87171' : '#f59e0b' }}>
                    {pred}%
                  </td>
                  <td style={{ padding: '12px', fontWeight: '700', color: '#f8fafc' }}>
                    {b.priority_score || 0}
                  </td>
                  <td style={{ padding: '12px' }}>
                    <span className={`glass-pill badge-${tier.toLowerCase()}`} style={{ padding: '3px 8px', borderRadius: '6px', fontSize: '10px', fontWeight: '700' }}>
                      {tier}
                    </span>
                  </td>
                  <td style={{ padding: '12px', fontSize: '11px', color: '#94a3b8' }}>
                    {b.recommended_action || 'MONITOR'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
