import os
import sqlite3
import datetime
from typing import List, Dict, Any, Optional
from backend.config import Config

try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False

class Database:
    _instance = None

    def __init__(self):
        self.use_supabase = bool(Config.SUPABASE_URL and Config.SUPABASE_KEY and HAS_SUPABASE)
        self.supabase: Optional[Client] = None
        if self.use_supabase:
            try:
                self.supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
                print(f"[DB] Connected to Supabase at {Config.SUPABASE_URL}")
            except Exception as e:
                print(f"[DB] Supabase connection failed: {e}. Falling back to SQLite.")
                self.use_supabase = False

        if not self.use_supabase:
            db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            os.makedirs(db_dir, exist_ok=True)
            self.sqlite_path = os.path.join(db_dir, "wasteflow.db")
            self._init_sqlite()
            print(f"[DB] Using Local SQLite DB at {self.sqlite_path}")

    def _get_sqlite_conn(self):
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite(self):
        conn = self._get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'driver',
                phone TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bins (
                id TEXT PRIMARY KEY,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                locality TEXT NOT NULL,
                collection_zone TEXT NOT NULL,
                area_type TEXT NOT NULL,
                bin_capacity_liters REAL NOT NULL DEFAULT 800.0,
                bin_type TEXT NOT NULL DEFAULT 'Mixed',
                installation_date TEXT,
                demand_multiplier REAL DEFAULT 1.0,
                sensor_noise_std_pct REAL DEFAULT 1.5,
                service_window TEXT DEFAULT '08:00-14:00',
                current_fill_level_pct REAL NOT NULL DEFAULT 20.0,
                last_collected_at TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bin_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                sensor_fill_level_pct REAL NOT NULL,
                temperature_c REAL DEFAULT 28.5,
                humidity_pct REAL DEFAULT 75.0,
                rainfall_mm REAL DEFAULT 0.0,
                is_holiday INTEGER DEFAULT 0,
                local_event INTEGER DEFAULT 0,
                sensor_anomaly INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (bin_id) REFERENCES bins(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collections (
                id TEXT PRIMARY KEY,
                bin_id TEXT NOT NULL,
                driver_id TEXT,
                collected_at TEXT DEFAULT (datetime('now')),
                fill_level_before_pct REAL NOT NULL,
                fill_level_after_pct REAL NOT NULL DEFAULT 0.0,
                collected_weight_kg REAL DEFAULT 0.0,
                route_stop_number INTEGER,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (bin_id) REFERENCES bins(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_state (
                id INTEGER PRIMARY KEY DEFAULT 1,
                virtual_time TEXT NOT NULL DEFAULT '2025-06-01T08:00:00+00:00',
                time_step_hours INTEGER NOT NULL DEFAULT 6,
                status TEXT NOT NULL DEFAULT 'running',
                last_advance_hours INTEGER DEFAULT 6,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO simulation_state (id, virtual_time, time_step_hours, status)
            VALUES (1, '2025-06-01T08:00:00+00:00', 6, 'running')
        """)
        conn.commit()
        conn.close()

    # ---------------- BINS ----------------
    def get_all_bins(self, active_only: bool = True) -> List[Dict[str, Any]]:
        if self.use_supabase and self.supabase:
            query = self.supabase.table("bins").select("*")
            if active_only:
                query = query.eq("active", True)
            res = query.order("id").execute()
            return res.data
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            if active_only:
                cursor.execute("SELECT * FROM bins WHERE active = 1 ORDER BY id")
            else:
                cursor.execute("SELECT * FROM bins ORDER BY id")
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return rows

    def get_bin(self, bin_id: str) -> Optional[Dict[str, Any]]:
        if self.use_supabase and self.supabase:
            res = self.supabase.table("bins").select("*").eq("id", bin_id).execute()
            return res.data[0] if res.data else None
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bins WHERE id = ?", (bin_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None

    def upsert_bins(self, bins_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not bins_data:
            return []
        if self.use_supabase and self.supabase:
            res = self.supabase.table("bins").upsert(bins_data).execute()
            return res.data
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            for b in bins_data:
                cols = list(b.keys())
                placeholders = ", ".join(["?"] * len(cols))
                updates = ", ".join([f"{col} = excluded.{col}" for col in cols if col != "id"])
                sql = f"""
                    INSERT INTO bins ({', '.join(cols)})
                    VALUES ({placeholders})
                    ON CONFLICT(id) DO UPDATE SET {updates}
                """
                cursor.execute(sql, list(b.values()))
            conn.commit()
            conn.close()
            return bins_data

    def update_bin_fill(self, bin_id: str, new_fill: float, last_collected_at: Optional[str] = None):
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if self.use_supabase and self.supabase:
            payload = {"current_fill_level_pct": new_fill, "updated_at": now_str}
            if last_collected_at:
                payload["last_collected_at"] = last_collected_at
            self.supabase.table("bins").update(payload).eq("id", bin_id).execute()
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            if last_collected_at:
                cursor.execute(
                    "UPDATE bins SET current_fill_level_pct = ?, last_collected_at = ?, updated_at = ? WHERE id = ?",
                    (new_fill, last_collected_at, now_str, bin_id)
                )
            else:
                cursor.execute(
                    "UPDATE bins SET current_fill_level_pct = ?, updated_at = ? WHERE id = ?",
                    (new_fill, now_str, bin_id)
                )
            conn.commit()
            conn.close()

    def update_multiple_bin_fills(self, fills_dict: Dict[str, float]):
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if self.use_supabase and self.supabase:
            all_bins = self.get_all_bins(active_only=False)
            records = []
            for b in all_bins:
                b_id = b["id"]
                if b_id in fills_dict:
                    b_copy = dict(b)
                    b_copy["current_fill_level_pct"] = fills_dict[b_id]
                    b_copy["updated_at"] = now_str
                    records.append(b_copy)
            if records:
                self.supabase.table("bins").upsert(records).execute()
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            for b_id, fill in fills_dict.items():
                cursor.execute("UPDATE bins SET current_fill_level_pct = ?, updated_at = ? WHERE id = ?", (fill, now_str, b_id))
            conn.commit()
            conn.close()

    def clear_telemetry_and_collections(self):
        if self.use_supabase and self.supabase:
            self.supabase.table("telemetry").delete().neq("id", -1).execute()
            self.supabase.table("collections").delete().neq("bin_id", "NONE").execute()
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM telemetry")
            cursor.execute("DELETE FROM collections")
            conn.commit()
            conn.close()

    # ---------------- TELEMETRY ----------------
    def insert_telemetry(self, telemetry_rows: List[Dict[str, Any]]) -> int:
        if not telemetry_rows:
            return 0
        if self.use_supabase and self.supabase:
            # Batch in chunks of 500
            chunk_size = 500
            for i in range(0, len(telemetry_rows), chunk_size):
                chunk = telemetry_rows[i:i + chunk_size]
                self.supabase.table("telemetry").insert(chunk).execute()
            return len(telemetry_rows)
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            first = telemetry_rows[0]
            cols = list(first.keys())
            placeholders = ", ".join(["?"] * len(cols))
            sql = f"INSERT INTO telemetry ({', '.join(cols)}) VALUES ({placeholders})"
            data = [[r.get(c) for c in cols] for r in telemetry_rows]
            cursor.executemany(sql, data)
            conn.commit()
            conn.close()
            return len(telemetry_rows)

    def get_bin_telemetry_history(self, bin_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        if self.use_supabase and self.supabase:
            res = self.supabase.table("telemetry").select("*")\
                .eq("bin_id", bin_id)\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            return res.data
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM telemetry WHERE bin_id = ? ORDER BY timestamp DESC LIMIT ?",
                (bin_id, limit)
            )
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return rows

    def get_all_recent_telemetry(self, limit_per_bin: int = 48) -> List[Dict[str, Any]]:
        if self.use_supabase and self.supabase:
            res = self.supabase.table("telemetry").select("*")\
                .order("timestamp", desc=True)\
                .limit(limit_per_bin * 25)\
                .execute()
            return res.data
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT ?", (limit_per_bin * 30,))
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return rows

    # ---------------- SIMULATION STATE ----------------
    def get_simulation_state(self) -> Dict[str, Any]:
        if self.use_supabase and self.supabase:
            res = self.supabase.table("simulation_state").select("*").eq("id", 1).execute()
            if res.data:
                return res.data[0]
            # default fallback
            return {"id": 1, "virtual_time": "2025-06-01T08:00:00+00:00", "time_step_hours": 6, "status": "running"}
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM simulation_state WHERE id = 1")
            row = cursor.fetchone()
            conn.close()
            if row:
                return dict(row)
            return {"id": 1, "virtual_time": "2025-06-01T08:00:00+00:00", "time_step_hours": 6, "status": "running"}

    def update_simulation_state(self, virtual_time: str, last_advance_hours: int = 6):
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if self.use_supabase and self.supabase:
            self.supabase.table("simulation_state").upsert({
                "id": 1,
                "virtual_time": virtual_time,
                "last_advance_hours": last_advance_hours,
                "updated_at": now_str
            }).execute()
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE simulation_state
                SET virtual_time = ?, last_advance_hours = ?, updated_at = ?
                WHERE id = 1
            """, (virtual_time, last_advance_hours, now_str))
            conn.commit()
            conn.close()

    # ---------------- COLLECTIONS ----------------
    def insert_collection(self, collection_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.use_supabase and self.supabase:
            res = self.supabase.table("collections").insert(collection_data).execute()
            return res.data[0] if res.data else collection_data
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            cols = list(collection_data.keys())
            placeholders = ", ".join(["?"] * len(cols))
            sql = f"INSERT INTO collections ({', '.join(cols)}) VALUES ({placeholders})"
            cursor.execute(sql, list(collection_data.values()))
            conn.commit()
            conn.close()
            return collection_data

    def get_recent_collections(self, limit: int = 20) -> List[Dict[str, Any]]:
        if self.use_supabase and self.supabase:
            res = self.supabase.table("collections").select("*").order("collected_at", desc=True).limit(limit).execute()
            return res.data
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM collections ORDER BY collected_at DESC LIMIT ?", (limit,))
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return rows

    # ---------------- PROFILES ----------------
    def upsert_profiles(self, profiles_data: List[Dict[str, Any]]):
        if not profiles_data:
            return
        if self.use_supabase and self.supabase:
            self.supabase.table("profiles").upsert(profiles_data).execute()
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            for p in profiles_data:
                cols = list(p.keys())
                placeholders = ", ".join(["?"] * len(cols))
                updates = ", ".join([f"{col} = excluded.{col}" for col in cols if col != "id"])
                sql = f"""
                    INSERT INTO profiles ({', '.join(cols)})
                    VALUES ({placeholders})
                    ON CONFLICT(id) DO UPDATE SET {updates}
                """
                cursor.execute(sql, list(p.values()))
            conn.commit()
            conn.close()

db = Database()
