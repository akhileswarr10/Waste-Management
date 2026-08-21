import React, { useState } from 'react';
import { Shield, Truck, Lock, User, ArrowRight, Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';
import { API_BASE_URL } from '../supabase';

export default function LoginPage({ onLoginSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [selectedRole, setSelectedRole] = useState('admin'); // 'admin' | 'driver'
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    setErrorMsg('');
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();

      if (res.ok && data.status === 'success') {
        onLoginSuccess(data.user);
      } else {
        setErrorMsg(data.message || 'Invalid username or password.');
      }
    } catch (err) {
      setErrorMsg('Failed to connect to backend server. Ensure Flask API is running.');
    } finally {
      setLoading(false);
    }
  };

  const setDemoCredentials = (role) => {
    setSelectedRole(role);
    if (role === 'admin') {
      setUsername('admin');
      setPassword('admin');
    } else {
      setUsername('driver');
      setPassword('driver');
    }
    setErrorMsg('');
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      background: 'radial-gradient(circle at 50% 20%, rgba(16, 185, 129, 0.15) 0%, rgba(15, 23, 42, 0.95) 75%), #0a0f1d',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Background Glow Blobs */}
      <div style={{
        position: 'absolute',
        top: '10%',
        left: '15%',
        width: '350px',
        height: '350px',
        background: 'radial-gradient(circle, rgba(16, 185, 129, 0.2) 0%, rgba(0,0,0,0) 70%)',
        borderRadius: '50%',
        filter: 'blur(40px)',
        pointerEvents: 'none'
      }}></div>

      <div style={{
        position: 'absolute',
        bottom: '15%',
        right: '15%',
        width: '400px',
        height: '400px',
        background: 'radial-gradient(circle, rgba(99, 102, 241, 0.18) 0%, rgba(0,0,0,0) 70%)',
        borderRadius: '50%',
        filter: 'blur(50px)',
        pointerEvents: 'none'
      }}></div>

      {/* Login Card Container */}
      <div className="glass-panel login-card-responsive" style={{
        width: '100%',
        maxWidth: '460px',
        padding: '36px 32px',
        borderRadius: '24px',
        border: '1px solid rgba(255, 255, 255, 0.12)',
        boxShadow: '0 25px 60px -15px rgba(0, 0, 0, 0.7), 0 0 35px rgba(16, 185, 129, 0.15)',
        position: 'relative',
        zIndex: 10
      }}>
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '56px',
            height: '56px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            boxShadow: '0 8px 20px rgba(16, 185, 129, 0.4)',
            marginBottom: '16px'
          }}>
            <Sparkles size={28} color="#ffffff" />
          </div>

          <h1 style={{ fontSize: '24px', fontWeight: '800', color: '#f8fafc', letterSpacing: '-0.02em', margin: 0 }}>
            WasteFlow AI
          </h1>
          <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '6px' }}>
            Smart Predictive Waste Management & Greedy Optimizer
          </p>
        </div>

        {/* Quick Portal Selector */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '8px',
          padding: '4px',
          borderRadius: '14px',
          background: 'rgba(0, 0, 0, 0.35)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          marginBottom: '24px'
        }}>
          <button
            type="button"
            onClick={() => setDemoCredentials('admin')}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '10px 14px',
              borderRadius: '10px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: '700',
              fontSize: '13px',
              transition: 'all 0.2s',
              background: selectedRole === 'admin' ? 'linear-gradient(135deg, #10b981, #059669)' : 'transparent',
              color: selectedRole === 'admin' ? '#ffffff' : '#94a3b8',
              boxShadow: selectedRole === 'admin' ? '0 4px 12px rgba(16, 185, 129, 0.35)' : 'none'
            }}
          >
            <Shield size={16} />
            Admin Portal
          </button>

          <button
            type="button"
            onClick={() => setDemoCredentials('driver')}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '10px 14px',
              borderRadius: '10px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: '700',
              fontSize: '13px',
              transition: 'all 0.2s',
              background: selectedRole === 'driver' ? 'linear-gradient(135deg, #6366f1, #4f46e5)' : 'transparent',
              color: selectedRole === 'driver' ? '#ffffff' : '#94a3b8',
              boxShadow: selectedRole === 'driver' ? '0 4px 12px rgba(99, 102, 241, 0.35)' : 'none'
            }}
          >
            <Truck size={16} />
            Driver Terminal
          </button>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 14px',
            borderRadius: '10px',
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#f87171',
            fontSize: '12px',
            fontWeight: '600',
            marginBottom: '18px'
          }}>
            <AlertCircle size={16} />
            {errorMsg}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#cbd5e1', marginBottom: '6px' }}>
              Username
            </label>
            <div style={{ position: 'relative' }}>
              <User size={16} color="#64748b" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username (e.g. admin or driver)"
                required
                style={{
                  width: '100%',
                  padding: '11px 12px 11px 38px',
                  borderRadius: '10px',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  background: 'rgba(15, 23, 42, 0.6)',
                  color: '#ffffff',
                  fontSize: '13px',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#cbd5e1', marginBottom: '6px' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} color="#64748b" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                required
                style={{
                  width: '100%',
                  padding: '11px 12px 11px 38px',
                  borderRadius: '10px',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  background: 'rgba(15, 23, 42, 0.6)',
                  color: '#ffffff',
                  fontSize: '13px',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
              />
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            style={{
              marginTop: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '12px 20px',
              borderRadius: '12px',
              border: 'none',
              cursor: loading ? 'not-allowed' : 'pointer',
              background: selectedRole === 'admin' ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)' : 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
              color: '#ffffff',
              fontWeight: '700',
              fontSize: '14px',
              boxShadow: selectedRole === 'admin' ? '0 6px 18px rgba(16, 185, 129, 0.4)' : '0 6px 18px rgba(99, 102, 241, 0.4)',
              transition: 'transform 0.15s, opacity 0.2s',
              opacity: loading ? 0.7 : 1
            }}
          >
            {loading ? 'Authenticating...' : `Log In to ${selectedRole === 'admin' ? 'Admin Hub' : 'Driver Terminal'}`}
            {!loading && <ArrowRight size={16} />}
          </button>
        </form>

        {/* Quick Credentials Helper */}
        <div style={{
          marginTop: '24px',
          padding: '12px 14px',
          borderRadius: '12px',
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px dashed rgba(255, 255, 255, 0.12)',
          fontSize: '11px',
          color: '#94a3b8',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px'
        }}>
          <div style={{ fontWeight: '700', color: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <CheckCircle2 size={13} color="#10b981" />
            Quick Demo Login Credentials:
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2px' }}>
            <span><strong>Admin:</strong> <code>admin</code> / <code>admin</code></span>
            <span style={{ color: 'rgba(255,255,255,0.2)' }}>|</span>
            <span><strong>Driver:</strong> <code>driver</code> / <code>driver</code></span>
          </div>
        </div>
      </div>
    </div>
  );
}
