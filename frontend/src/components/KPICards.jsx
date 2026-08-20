import React from 'react';
import { Trash2, AlertTriangle, TrendingUp, DollarSign, Fuel, CheckCircle2 } from 'lucide-react';

export default function KPICards({ predictionsSummary, routeSummary }) {
  const totalBins = predictionsSummary?.total_bins || 20;
  const atRisk = predictionsSummary?.at_risk_bins_count || 0;
  const avgCurrent = predictionsSummary?.average_current_fill_pct || 0;
  const avgPredicted = predictionsSummary?.average_predicted_fill_pct || 0;
  const fuelSavings = routeSummary?.fuel_savings_pct || 28.5;
  const distSaved = routeSummary?.distance_saved_km || 7.57;
  const costSaved = routeSummary?.estimated_cost_savings_inr || 306.79;

  const cards = [
    {
      label: 'Total Smart Bins',
      value: totalBins,
      subtext: 'Active IoT Telemetry Nodes',
      icon: Trash2,
      color: '#10b981',
      bgGlow: 'rgba(16, 185, 129, 0.12)'
    },
    {
      label: 'Bins at Risk (High / Crit)',
      value: atRisk,
      subtext: `${totalBins - atRisk} bins in normal status`,
      icon: AlertTriangle,
      color: atRisk > 0 ? '#ef4444' : '#10b981',
      bgGlow: atRisk > 0 ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.12)',
      badge: atRisk > 0 ? 'ACTION REQUIRED' : 'ALL CLEAR'
    },
    {
      label: 'Average Fill / 6h Pred',
      value: `${avgCurrent}% → ${avgPredicted}%`,
      subtext: 'ML Regression 6h Forecast',
      icon: TrendingUp,
      color: '#f59e0b',
      bgGlow: 'rgba(245, 158, 11, 0.12)'
    },
    {
      label: 'Greedy Route Fuel Savings',
      value: `${fuelSavings}%`,
      subtext: `Saved ${distSaved} km (₹${costSaved})`,
      icon: Fuel,
      color: '#6366f1',
      bgGlow: 'rgba(99, 102, 241, 0.15)'
    }
  ];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
      gap: '16px',
      margin: '0 16px 16px 16px'
    }}>
      {cards.map((c, i) => {
        const Icon = c.icon;
        return (
          <div key={i} className="glass-panel" style={{
            padding: '18px 20px',
            position: 'relative',
            overflow: 'hidden',
            transition: 'transform 0.2s, box-shadow 0.2s',
            cursor: 'default'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  {c.label}
                </span>
                <h3 style={{ fontSize: '24px', fontWeight: '800', marginTop: '6px', color: '#ffffff' }}>
                  {c.value}
                </h3>
              </div>
              <div style={{
                width: '42px',
                height: '42px',
                borderRadius: '10px',
                background: c.bgGlow,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: `1px solid ${c.color}30`
              }}>
                <Icon size={20} color={c.color} />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px', paddingTop: '10px', borderTop: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                {c.subtext}
              </span>
              {c.badge && (
                <span className="glass-pill" style={{ fontSize: '10px', fontWeight: '700', padding: '2px 6px', borderRadius: '6px', color: c.color, border: `1px solid ${c.color}40` }}>
                  {c.badge}
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
