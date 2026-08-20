-- ============================================================
-- WASTEFLOW - SMART WASTE MANAGEMENT SYSTEM
-- COMPLETE SUPABASE POSTGRESQL SCHEMA & POLICIES
-- ============================================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. ENUMS & TYPES
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('admin', 'driver', 'operator');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 3. PROFILES TABLE (User Roles & Auth Linkage)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'driver' CHECK (role IN ('admin', 'driver', 'operator')),
    phone TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. BINS TABLE
CREATE TABLE IF NOT EXISTS bins (
    id TEXT PRIMARY KEY,                          -- e.g., 'B0001'
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    locality TEXT NOT NULL,                       -- e.g., 'East', 'West', 'North', 'South', 'Central'
    collection_zone TEXT NOT NULL,                -- e.g., 'Z1', 'Z2', 'Z3', 'Z4', 'Z5'
    area_type TEXT NOT NULL,                      -- e.g., 'Commercial', 'Residential', 'Industrial', 'School', 'Market', 'Public_Park', 'Hospital'
    bin_capacity_liters DOUBLE PRECISION NOT NULL DEFAULT 800.0,
    bin_type TEXT NOT NULL DEFAULT 'Mixed',       -- 'Mixed', 'Organic', 'Recyclable'
    installation_date DATE DEFAULT CURRENT_DATE,
    demand_multiplier DOUBLE PRECISION DEFAULT 1.0,
    sensor_noise_std_pct DOUBLE PRECISION DEFAULT 1.5,
    service_window TEXT DEFAULT '08:00-14:00',
    current_fill_level_pct DOUBLE PRECISION NOT NULL DEFAULT 20.0,
    last_collected_at TIMESTAMPTZ DEFAULT NOW(),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. TELEMETRY TABLE (Time-series sensor readings & environmental context)
CREATE TABLE IF NOT EXISTS telemetry (
    id BIGSERIAL PRIMARY KEY,
    bin_id TEXT NOT NULL REFERENCES bins(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    sensor_fill_level_pct DOUBLE PRECISION NOT NULL,
    temperature_c DOUBLE PRECISION DEFAULT 28.5,
    humidity_pct DOUBLE PRECISION DEFAULT 75.0,
    rainfall_mm DOUBLE PRECISION DEFAULT 0.0,
    is_holiday INTEGER DEFAULT 0,
    local_event INTEGER DEFAULT 0,
    sensor_anomaly INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast time-series & lag queries per bin
CREATE INDEX IF NOT EXISTS idx_telemetry_bin_timestamp ON telemetry(bin_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry(timestamp DESC);

-- 6. COLLECTIONS TABLE (Driver pickup records)
CREATE TABLE IF NOT EXISTS collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bin_id TEXT NOT NULL REFERENCES bins(id) ON DELETE CASCADE,
    driver_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    fill_level_before_pct DOUBLE PRECISION NOT NULL,
    fill_level_after_pct DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    collected_weight_kg DOUBLE PRECISION DEFAULT 0.0,
    route_stop_number INTEGER,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_collections_bin_id ON collections(bin_id);
CREATE INDEX IF NOT EXISTS idx_collections_collected_at ON collections(collected_at DESC);

-- 7. SIMULATION STATE TABLE (Virtual Clock & Engine Control)
CREATE TABLE IF NOT EXISTS simulation_state (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    virtual_time TIMESTAMPTZ NOT NULL DEFAULT '2025-06-01 08:00:00+00',
    time_step_hours INTEGER NOT NULL DEFAULT 6,
    status TEXT NOT NULL DEFAULT 'running',
    last_advance_hours INTEGER DEFAULT 6,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure singleton row exists in simulation_state
INSERT INTO simulation_state (id, virtual_time, time_step_hours, status)
VALUES (1, '2025-06-01 08:00:00+00', 6, 'running')
ON CONFLICT (id) DO NOTHING;

-- 8. ROW LEVEL SECURITY (RLS) POLICIES
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE bins ENABLE ROW LEVEL SECURITY;
ALTER TABLE telemetry ENABLE ROW LEVEL SECURITY;
ALTER TABLE collections ENABLE ROW LEVEL SECURITY;
ALTER TABLE simulation_state ENABLE ROW LEVEL SECURITY;

-- Allow public / authenticated read & write for app operations (or service role)
DROP POLICY IF EXISTS "Public full access on bins" ON bins;
CREATE POLICY "Public full access on bins" ON bins FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Public full access on telemetry" ON telemetry;
CREATE POLICY "Public full access on telemetry" ON telemetry FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Public full access on collections" ON collections;
CREATE POLICY "Public full access on collections" ON collections FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Public full access on simulation_state" ON simulation_state;
CREATE POLICY "Public full access on simulation_state" ON simulation_state FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Public full access on profiles" ON profiles;
CREATE POLICY "Public full access on profiles" ON profiles FOR ALL USING (true) WITH CHECK (true);
