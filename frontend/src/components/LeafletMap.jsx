import React, { useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Navigation, Zap, AlertCircle, Clock, CheckCircle } from 'lucide-react';

// Custom Map Marker Builder using HTML DivIcons
function createCustomPin(bin, stopNumber = null, isDepot = false) {
  if (isDepot) {
    return L.divIcon({
      className: 'custom-leaflet-pin',
      html: `
        <div class="bin-marker-pin bin-pin-depot" style="width: 36px; height: 36px; border-radius: 10px;">
          <span style="font-size: 16px;">🏢</span>
        </div>
      `,
      iconSize: [36, 36],
      iconAnchor: [18, 18],
      popupAnchor: [0, -20]
    });
  }

  const fill = bin.current_fill_level_pct || 0;
  let pinClass = 'bin-pin-low';
  let badgeColor = '#10b981';

  if (fill >= 100 || bin.urgency_tier === 'EMERGENCY') {
    pinClass = 'bin-pin-emergency';
    badgeColor = '#dc2626';
  } else if (fill >= 90 || bin.urgency_tier === 'CRITICAL') {
    pinClass = 'bin-pin-critical';
    badgeColor = '#ef4444';
  } else if (fill >= 75 || bin.urgency_tier === 'HIGH') {
    pinClass = 'bin-pin-high';
    badgeColor = '#f97316';
  } else if (fill >= 50 || bin.urgency_tier === 'MEDIUM') {
    pinClass = 'bin-pin-med';
    badgeColor = '#f59e0b';
  }

  const label = stopNumber !== null && stopNumber !== undefined ? `#${stopNumber}` : `${Math.round(fill)}%`;

  return L.divIcon({
    className: 'custom-leaflet-pin',
    html: `
      <div class="bin-marker-pin ${pinClass}" style="width: 32px; height: 32px;">
        <span>${label}</span>
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -18]
  });
}

export default function LeafletMap({
  bins = [],
  depot = { latitude: 10.015, longitude: 76.345 },
  routeStops = [],
  polylineCoordinates = [],
  showRoute = true,
  onCollectBin = null
}) {
  // Map Center around Central Kochi
  const center = useMemo(() => [depot?.latitude || 10.015, depot?.longitude || 76.345], [depot]);

  // Index of stops for fast stop_number lookup
  const stopNumberMap = useMemo(() => {
    const map = {};
    routeStops.forEach(s => {
      if (s.bin_id && !s.is_depot) {
        map[s.bin_id] = s.stop_number;
      }
    });
    return map;
  }, [routeStops]);

  return (
    <div className="glass-panel" style={{ height: '520px', width: '100%', position: 'relative', overflow: 'hidden' }}>
      <MapContainer
        center={center}
        zoom={13}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%' }}
      >
        {/* Modern Dark/Carto Tile Layer */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        />

        {/* Central Operations Depot Marker */}
        <Marker
          position={[depot.latitude, depot.longitude]}
          icon={createCustomPin(null, null, true)}
        >
          <Popup>
            <div style={{ padding: '6px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                <span style={{ fontSize: '18px' }}>🏢</span>
                <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#818cf8', margin: 0 }}>
                  Central Operations Base
                </h4>
              </div>
              <p style={{ fontSize: '12px', color: '#cbd5e1', margin: 0 }}>
                Vehicle Depot & Municipal Routing Hub
              </p>
              <div style={{ marginTop: '8px', fontSize: '11px', color: '#94a3b8', fontFamily: 'monospace' }}>
                Lat: {depot.latitude} | Lon: {depot.longitude}
              </div>
            </div>
          </Popup>
        </Marker>

        {/* All Smart Bins Markers */}
        {bins.map((bin) => {
          const isStop = stopNumberMap[bin.bin_id] !== undefined;
          const stopNum = isStop ? stopNumberMap[bin.bin_id] : null;

          return (
            <Marker
              key={bin.bin_id}
              position={[bin.latitude, bin.longitude]}
              icon={createCustomPin(bin, showRoute ? stopNum : null, false)}
            >
              <Popup>
                <div style={{ padding: '8px', minWidth: '220px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontWeight: '800', fontSize: '15px', color: '#f8fafc' }}>
                        {bin.bin_id}
                      </span>
                      <span className="glass-pill" style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '6px', color: '#94a3b8' }}>
                        {bin.collection_zone || 'Z1'}
                      </span>
                    </div>

                    <span className={`glass-pill badge-${(bin.urgency_tier || 'LOW').toLowerCase()}`} style={{ fontSize: '10px', fontWeight: '700', padding: '2px 6px', borderRadius: '6px' }}>
                      {bin.urgency_tier || 'NORMAL'}
                    </span>
                  </div>

                  <p style={{ fontSize: '12px', color: '#cbd5e1', marginBottom: '10px' }}>
                    <strong>{bin.area_type}</strong> ({bin.locality} Locality)
                  </p>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '10px' }}>
                    <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '6px 8px', borderRadius: '8px' }}>
                      <span style={{ fontSize: '10px', color: '#94a3b8', display: 'block' }}>Current Fill</span>
                      <span style={{ fontSize: '14px', fontWeight: '700', color: bin.current_fill_level_pct >= 80 ? '#ef4444' : '#10b981' }}>
                        {bin.current_fill_level_pct}%
                      </span>
                    </div>

                    <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '6px 8px', borderRadius: '8px' }}>
                      <span style={{ fontSize: '10px', color: '#94a3b8', display: 'block' }}>6h Predicted</span>
                      <span style={{ fontSize: '14px', fontWeight: '700', color: '#f59e0b' }}>
                        {bin.predicted_fill_6h_pct || bin.current_fill_level_pct}%
                      </span>
                    </div>
                  </div>

                  <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '8px' }}>
                    <div>Priority Score: <strong style={{ color: '#f8fafc' }}>{bin.priority_score || 0}/100</strong></div>
                    <div>Capacity: <strong style={{ color: '#f8fafc' }}>{bin.bin_capacity_liters} Liters</strong></div>
                  </div>

                  {onCollectBin && (
                    <button
                      onClick={() => onCollectBin(bin.bin_id)}
                      style={{
                        width: '100%',
                        padding: '6px',
                        borderRadius: '8px',
                        border: 'none',
                        background: 'linear-gradient(135deg, #10b981, #059669)',
                        color: '#ffffff',
                        fontWeight: '700',
                        fontSize: '12px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px'
                      }}
                    >
                      <CheckCircle size={14} />
                      Collect Now (Reset 0%)
                    </button>
                  )}
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* Exact Real Road Polyline (snapped to street network) */}
        {showRoute && polylineCoordinates.length > 1 && (
          <>
            {/* Road Casing / Border */}
            <Polyline
              positions={polylineCoordinates}
              pathOptions={{
                color: '#1e1b4b',
                weight: 8,
                opacity: 0.9,
                lineCap: 'round',
                lineJoin: 'round'
              }}
            />
            {/* Road Navigation Core */}
            <Polyline
              positions={polylineCoordinates}
              pathOptions={{
                color: '#6366f1',
                weight: 5,
                opacity: 0.95,
                lineCap: 'round',
                lineJoin: 'round'
              }}
            />
            {/* Inner Direction Glow */}
            <Polyline
              positions={polylineCoordinates}
              pathOptions={{
                color: '#a5b4fc',
                weight: 2,
                opacity: 0.8,
                lineCap: 'round',
                lineJoin: 'round'
              }}
            />
          </>
        )}
      </MapContainer>

      {/* Map Legend Overlay */}
      <div className="glass-panel" style={{
        position: 'absolute',
        bottom: '16px',
        right: '16px',
        padding: '10px 14px',
        zIndex: 1000,
        fontSize: '11px',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
        boxShadow: '0 8px 24px rgba(0,0,0,0.5)'
      }}>
        <span style={{ fontWeight: '700', color: '#f8fafc', marginBottom: '2px' }}>Fill Urgency Legend</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#10b981' }} />
          <span style={{ color: '#cbd5e1' }}>Low (&lt;50%) - Skip</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f59e0b' }} />
          <span style={{ color: '#cbd5e1' }}>Medium (50-74%) - On-the-Way</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f97316' }} />
          <span style={{ color: '#cbd5e1' }}>High (75-89%) - Primary Target</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444', boxShadow: '0 0 8px #ef4444' }} />
          <span style={{ color: '#cbd5e1' }}>Critical (&ge;90%) - Urgent</span>
        </div>
      </div>
    </div>
  );
}
