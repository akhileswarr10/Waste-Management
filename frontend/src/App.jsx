import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import LoginPage from './components/LoginPage';
import KPICards from './components/KPICards';
import SimulationToolbar from './components/SimulationToolbar';
import LeafletMap from './components/LeafletMap';
import BinsTable from './components/BinsTable';
import RoutePanel from './components/RoutePanel';
import { API_BASE_URL } from './supabase';
import { Layers, Map, List, Navigation, ShieldCheck, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react';

export default function App() {
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = localStorage.getItem('wasteflow_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [activeRole, setActiveRole] = useState(() => {
    try {
      const saved = localStorage.getItem('wasteflow_user');
      return saved ? (JSON.parse(saved).role || 'admin') : 'admin';
    } catch {
      return 'admin';
    }
  });

  const [activeTab, setActiveTab] = useState('map');      // 'map', 'table', 'route'
  const [loading, setLoading] = useState(true);
  const [advancing, setAdvancing] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [collectingBinId, setCollectingBinId] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  const handleLoginSuccess = (user) => {
    localStorage.setItem('wasteflow_user', JSON.stringify(user));
    setCurrentUser(user);
    setActiveRole(user.role || 'admin');
    showToast(`Welcome back, ${user.name}! Accessing ${user.role === 'admin' ? 'Admin Hub' : 'Driver Terminal'}.`);
  };

  const handleLogout = () => {
    localStorage.removeItem('wasteflow_user');
    setCurrentUser(null);
    showToast('Logged out of session.');
  };

  // Core Data States
  const [virtualTime, setVirtualTime] = useState(null);
  const [predictionsData, setPredictionsData] = useState(null);
  const [routeData, setRouteData] = useState(null);

  const showToast = (msg, type = 'success') => {
    setToastMessage({ text: msg, type });
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Fetch all live backend data
  const fetchData = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    try {
      // 1. Simulation Status
      const simRes = await fetch(`${API_BASE_URL}/api/simulation/status`);
      const simJson = await simRes.json();
      if (simJson.status === 'success') {
        setVirtualTime(simJson.simulation_state?.virtual_time);
      }

      // 2. Predictions & Telemetry Features
      const predRes = await fetch(`${API_BASE_URL}/api/predictions`);
      const predJson = await predRes.json();
      if (predJson.status === 'success') {
        setPredictionsData(predJson.data);
      }

      // 3. Optimized Greedy Route
      const routeRes = await fetch(`${API_BASE_URL}/api/routes/optimized`);
      const routeJson = await routeRes.json();
      if (routeJson.status === 'success') {
        setRouteData(routeJson.data);
      }
    } catch (err) {
      console.error('Failed to fetch data:', err);
      showToast('Error connecting to backend API. Ensure Flask server is running.', 'error');
    } finally {
      if (!quiet) setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Advance Time Action (+6h or +24h)
  const handleAdvanceTime = async (hours) => {
    setAdvancing(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/simulation/advance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hours })
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast(`Simulation advanced by +${hours} hours! New telemetry recorded.`);
        await fetchData(true);
      } else {
        showToast(data.message || 'Advance failed', 'error');
      }
    } catch (err) {
      showToast('Network error during advance', 'error');
    } finally {
      setAdvancing(false);
    }
  };

  // Reset Simulation Action
  const handleResetSimulation = async () => {
    setResetting(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/simulation/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast('Simulation reset to initial baseline levels!');
        await fetchData(true);
      } else {
        showToast(data.message || 'Reset failed', 'error');
      }
    } catch (err) {
      showToast('Reset failed: check backend connection', 'error');
    } finally {
      setResetting(false);
    }
  };

  // Mark Single Bin as Collected
  const handleCollectBin = async (binId) => {
    setCollectingBinId(binId);
    try {
      const res = await fetch(`${API_BASE_URL}/api/bins/${binId}/collect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast(`Bin ${binId} marked as collected! Fill reset to 0%.`);
        await fetchData(true);
      } else {
        showToast(data.message || 'Collection failed', 'error');
      }
    } catch (err) {
      showToast('Error recording collection', 'error');
    } finally {
      setCollectingBinId(null);
    }
  };

  // Mark All Route Stops as Completed (Bulk Action)
  const [collectingAll, setCollectingAll] = useState(false);
  const handleCollectAll = async () => {
    setCollectingAll(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/routes/collect-all`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await res.json();
      if (data.status === 'success') {
        showToast(data.message || 'All route stops marked as collected!');
        await fetchData(true);
      } else {
        showToast(data.message || 'Bulk collection failed', 'error');
      }
    } catch (err) {
      showToast('Error during bulk collection', 'error');
    } finally {
      setCollectingAll(false);
    }
  };

  const bins = predictionsData?.predictions || [];
  const depot = routeData?.depot || { latitude: 10.015, longitude: 76.345 };
  const routeStops = routeData?.stops || [];
  const polylineCoords = routeData?.polyline_coordinates || [];

  if (!currentUser) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div style={{ paddingBottom: '32px' }}>
      {/* Navbar */}
      <Navbar
        virtualTime={virtualTime}
        activeRole={activeRole}
        setActiveRole={setActiveRole}
        onRefresh={() => fetchData()}
        loading={loading}
        currentUser={currentUser}
        onLogout={handleLogout}
      />

      {/* Toast Notification */}
      {toastMessage && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          zIndex: 9999,
          padding: '12px 20px',
          borderRadius: '12px',
          background: toastMessage.type === 'error' ? 'rgba(220, 38, 38, 0.95)' : 'rgba(16, 185, 129, 0.95)',
          color: '#ffffff',
          fontWeight: '600',
          fontSize: '13px',
          boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          {toastMessage.type === 'error' ? <AlertTriangle size={18} /> : <CheckCircle2 size={18} />}
          {toastMessage.text}
        </div>
      )}

      {/* High-Level KPI Summary Cards */}
      <KPICards
        predictionsSummary={predictionsData}
        routeSummary={routeData?.summary}
      />

      {/* Admin Simulation Controls */}
      {activeRole === 'admin' && (
        <SimulationToolbar
          onAdvanceTime={handleAdvanceTime}
          onResetSimulation={handleResetSimulation}
          onCollectAll={handleCollectAll}
          advancing={advancing}
          resetting={resetting}
          collectingAll={collectingAll}
        />
      )}

      {/* Main Content Layout */}
      <main style={{ margin: '0 16px', display: 'grid', gridTemplateColumns: activeRole === 'driver' ? '1fr 1.1fr' : '1.3fr 1fr', gap: '16px' }}>
        {/* Left Column: Interactive Map */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 4px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Map size={18} color="#10b981" />
              <h3 style={{ fontSize: '15px', fontWeight: '700', color: '#f8fafc' }}>
                {activeRole === 'driver' ? 'Driver Live Navigation Route' : 'Live Urban Bin Monitoring Map'}
              </h3>
            </div>

            <span className="glass-pill" style={{ padding: '3px 10px', borderRadius: '8px', fontSize: '11px', color: '#94a3b8' }}>
              Depot Base: {depot.latitude}, {depot.longitude}
            </span>
          </div>

          <LeafletMap
            bins={bins}
            depot={depot}
            routeStops={routeStops}
            polylineCoordinates={polylineCoords}
            showRoute={true}
            onCollectBin={handleCollectBin}
          />
        </div>

        {/* Right Column: Route Manifest (Driver) OR Multi-Tab Grid (Admin) */}
        <div>
          {activeRole === 'driver' ? (
            <RoutePanel
              routeData={routeData}
              onCollectBin={handleCollectBin}
              onCollectAll={handleCollectAll}
              collectingBinId={collectingBinId}
              collectingAll={collectingAll}
              isDriverView={true}
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', height: '100%' }}>
              {/* Tab Selector */}
              <div className="glass-pill" style={{ display: 'flex', padding: '4px', borderRadius: '10px', width: 'fit-content', gap: '4px' }}>
                <button
                  onClick={() => setActiveTab('map')}
                  style={{
                    padding: '6px 14px',
                    borderRadius: '6px',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '12px',
                    fontWeight: '600',
                    background: activeTab === 'map' ? 'rgba(255, 255, 255, 0.12)' : 'transparent',
                    color: activeTab === 'map' ? '#ffffff' : '#94a3b8'
                  }}
                >
                  Greedy Route Sequence
                </button>

                <button
                  onClick={() => setActiveTab('table')}
                  style={{
                    padding: '6px 14px',
                    borderRadius: '6px',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '12px',
                    fontWeight: '600',
                    background: activeTab === 'table' ? 'rgba(255, 255, 255, 0.12)' : 'transparent',
                    color: activeTab === 'table' ? '#ffffff' : '#94a3b8'
                  }}
                >
                  All 20 Bins Telemetry
                </button>
              </div>

              {/* Tab Views */}
              {activeTab === 'map' ? (
                <RoutePanel
                  routeData={routeData}
                  onCollectBin={handleCollectBin}
                  onCollectAll={handleCollectAll}
                  collectingBinId={collectingBinId}
                  collectingAll={collectingAll}
                  isDriverView={false}
                />
              ) : (
                <BinsTable
                  bins={bins}
                  onSelectBin={(bin) => console.log('Selected bin:', bin)}
                />
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
