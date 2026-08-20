import os
import sys
import random
import datetime

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.db import db

# Realistic 20 Bin Dataset (Derived from Kochi urban sector)
MOCK_BINS = [
    {
        "id": "B0001",
        "latitude": 10.018286,
        "longitude": 76.366415,
        "locality": "East",
        "collection_zone": "Z4",
        "area_type": "School",
        "bin_capacity_liters": 970.0,
        "bin_type": "Mixed",
        "installation_date": "2024-12-22",
        "demand_multiplier": 0.88,
        "sensor_noise_std_pct": 2.27,
        "service_window": "08:00-14:00",
        "current_fill_level_pct": 28.0,
        "active": True
    },
    {
        "id": "B0002",
        "latitude": 9.996269,
        "longitude": 76.297629,
        "locality": "West",
        "collection_zone": "Z5",
        "area_type": "Residential",
        "bin_capacity_liters": 680.0,
        "bin_type": "Mixed",
        "installation_date": "2025-01-17",
        "demand_multiplier": 1.05,
        "sensor_noise_std_pct": 1.65,
        "service_window": "08:00-14:00",
        "current_fill_level_pct": 54.0,
        "active": True
    },
    {
        "id": "B0003",
        "latitude": 9.994101,
        "longitude": 76.315717,
        "locality": "South",
        "collection_zone": "Z3",
        "area_type": "Commercial",
        "bin_capacity_liters": 954.0,
        "bin_type": "Mixed",
        "installation_date": "2025-04-07",
        "demand_multiplier": 0.85,
        "sensor_noise_std_pct": 2.10,
        "service_window": "06:00-12:00",
        "current_fill_level_pct": 68.0,
        "active": True
    },
    {
        "id": "B0004",
        "latitude": 10.023192,
        "longitude": 76.359705,
        "locality": "East",
        "collection_zone": "Z4",
        "area_type": "Industrial",
        "bin_capacity_liters": 1459.0,
        "bin_type": "Mixed",
        "installation_date": "2024-09-30",
        "demand_multiplier": 0.85,
        "sensor_noise_std_pct": 2.39,
        "service_window": "06:00-12:00",
        "current_fill_level_pct": 32.0,
        "active": True
    },
    {
        "id": "B0005",
        "latitude": 10.020928,
        "longitude": 76.374849,
        "locality": "East",
        "collection_zone": "Z4",
        "area_type": "School",
        "bin_capacity_liters": 834.0,
        "bin_type": "Mixed",
        "installation_date": "2024-09-22",
        "demand_multiplier": 0.84,
        "sensor_noise_std_pct": 1.43,
        "service_window": "08:00-14:00",
        "current_fill_level_pct": 22.0,
        "active": True
    },
    {
        "id": "B0006",
        "latitude": 9.995055,
        "longitude": 76.297809,
        "locality": "West",
        "collection_zone": "Z5",
        "area_type": "Market",
        "bin_capacity_liters": 1208.0,
        "bin_type": "Mixed",
        "installation_date": "2025-03-12",
        "demand_multiplier": 0.79,
        "sensor_noise_std_pct": 1.15,
        "service_window": "08:00-14:00",
        "current_fill_level_pct": 84.0,
        "active": True
    },
    {
        "id": "B0007",
        "latitude": 10.030795,
        "longitude": 76.344180,
        "locality": "North",
        "collection_zone": "Z2",
        "area_type": "Public_Park",
        "bin_capacity_liters": 617.0,
        "bin_type": "Mixed",
        "installation_date": "2025-04-04",
        "demand_multiplier": 1.05,
        "sensor_noise_std_pct": 1.34,
        "service_window": "12:00-18:00",
        "current_fill_level_pct": 36.0,
        "active": True
    },
    {
        "id": "B0008",
        "latitude": 10.035106,
        "longitude": 76.345539,
        "locality": "North",
        "collection_zone": "Z2",
        "area_type": "Residential",
        "bin_capacity_liters": 887.0,
        "bin_type": "Organic",
        "installation_date": "2025-04-26",
        "demand_multiplier": 1.17,
        "sensor_noise_std_pct": 1.79,
        "service_window": "08:00-14:00",
        "current_fill_level_pct": 58.0,
        "active": True
    },
    {
        "id": "B0009",
        "latitude": 9.989792,
        "longitude": 76.313870,
        "locality": "South",
        "collection_zone": "Z3",
        "area_type": "Commercial",
        "bin_capacity_liters": 740.0,
        "bin_type": "Organic",
        "installation_date": "2025-04-20",
        "demand_multiplier": 1.05,
        "sensor_noise_std_pct": 1.80,
        "service_window": "06:00-12:00",
        "current_fill_level_pct": 89.0,
        "active": True
    },
    {
        "id": "B0010",
        "latitude": 10.025319,
        "longitude": 76.372587,
        "locality": "East",
        "collection_zone": "Z4",
        "area_type": "Industrial",
        "bin_capacity_liters": 1163.0,
        "bin_type": "Mixed",
        "installation_date": "2024-09-11",
        "demand_multiplier": 0.93,
        "sensor_noise_std_pct": 1.07,
        "service_window": "08:00-14:00",
        "current_fill_level_pct": 41.0,
        "active": True
    },
    {
        "id": "B0011",
        "latitude": 10.023262,
        "longitude": 76.369587,
        "locality": "East",
        "collection_zone": "Z4",
        "area_type": "Commercial",
        "bin_capacity_liters": 741.0,
        "bin_type": "Mixed",
        "installation_date": "2025-04-05",
        "demand_multiplier": 1.04,
        "sensor_noise_std_pct": 1.57,
        "service_window": "06:00-12:00",
        "current_fill_level_pct": 86.0,
        "active": True
    },
    {
        "id": "B0012",
        "latitude": 10.030763,
        "longitude": 76.348688,
        "locality": "North",
        "collection_zone": "Z2",
        "area_type": "Commercial",
        "bin_capacity_liters": 883.0,
        "bin_type": "Mixed",
        "installation_date": "2025-05-01",
        "demand_multiplier": 0.93,
        "sensor_noise_std_pct": 1.30,
        "service_window": "08:00-14:00",
        "current_fill_level_pct": 52.0,
        "active": True
    },
    {
        "id": "B0013",
        "latitude": 10.014197,
        "longitude": 76.359986,
        "locality": "East",
        "collection_zone": "Z4",
        "area_type": "School",
        "bin_capacity_liters": 601.0,
        "bin_type": "Organic",
        "installation_date": "2024-12-25",
        "demand_multiplier": 1.00,
        "sensor_noise_std_pct": 1.17,
        "service_window": "08:00-14:00",
        "current_fill_level_pct": 25.0,
        "active": True
    },
    {
        "id": "B0014",
        "latitude": 10.003340,
        "longitude": 76.296482,
        "locality": "West",
        "collection_zone": "Z5",
        "area_type": "Commercial",
        "bin_capacity_liters": 979.0,
        "bin_type": "Mixed",
        "installation_date": "2025-03-06",
        "demand_multiplier": 0.93,
        "sensor_noise_std_pct": 1.26,
        "service_window": "08:00-14:00",
        "current_fill_level_pct": 62.0,
        "active": True
    },
    {
        "id": "B0015",
        "latitude": 10.019577,
        "longitude": 76.365418,
        "locality": "East",
        "collection_zone": "Z4",
        "area_type": "Residential",
        "bin_capacity_liters": 787.0,
        "bin_type": "Mixed",
        "installation_date": "2025-02-13",
        "demand_multiplier": 0.90,
        "sensor_noise_std_pct": 1.52,
        "service_window": "08:00-14:00",
        "current_fill_level_pct": 31.0,
        "active": True
    },
    {
        "id": "B0016",
        "latitude": 10.021530,
        "longitude": 76.367393,
        "locality": "East",
        "collection_zone": "Z4",
        "area_type": "Industrial",
        "bin_capacity_liters": 1549.0,
        "bin_type": "Mixed",
        "installation_date": "2024-09-12",
        "demand_multiplier": 1.13,
        "sensor_noise_std_pct": 1.51,
        "service_window": "08:00-14:00",
        "current_fill_level_pct": 45.0,
        "active": True
    },
    {
        "id": "B0017",
        "latitude": 10.012697,
        "longitude": 76.330334,
        "locality": "Central",
        "collection_zone": "Z1",
        "area_type": "Residential",
        "bin_capacity_liters": 793.0,
        "bin_type": "Mixed",
        "installation_date": "2025-03-05",
        "demand_multiplier": 0.90,
        "sensor_noise_std_pct": 1.16,
        "service_window": "08:00-14:00",
        "current_fill_level_pct": 49.0,
        "active": True
    },
    {
        "id": "B0018",
        "latitude": 10.018167,
        "longitude": 76.361122,
        "locality": "East",
        "collection_zone": "Z4",
        "area_type": "Market",
        "bin_capacity_liters": 1324.0,
        "bin_type": "Mixed",
        "installation_date": "2025-05-11",
        "demand_multiplier": 1.02,
        "sensor_noise_std_pct": 0.88,
        "service_window": "06:00-12:00",
        "current_fill_level_pct": 91.0,
        "active": True
    },
    {
        "id": "B0019",
        "latitude": 10.017822,
        "longitude": 76.361455,
        "locality": "East",
        "collection_zone": "Z4",
        "area_type": "Hospital",
        "bin_capacity_liters": 1162.0,
        "bin_type": "Mixed",
        "installation_date": "2024-12-12",
        "demand_multiplier": 1.18,
        "sensor_noise_std_pct": 2.19,
        "service_window": "08:00-14:00",
        "current_fill_level_pct": 55.0,
        "active": True
    },
    {
        "id": "B0020",
        "latitude": 10.013467,
        "longitude": 76.330813,
        "locality": "Central",
        "collection_zone": "Z1",
        "area_type": "Residential",
        "bin_capacity_liters": 874.0,
        "bin_type": "Mixed",
        "installation_date": "2024-10-07",
        "demand_multiplier": 1.02,
        "sensor_noise_std_pct": 2.38,
        "service_window": "06:00-12:00",
        "current_fill_level_pct": 82.0,
        "active": True
    }
]

MOCK_PROFILES = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "email": "admin@wasteflow.io",
        "full_name": "Admin Officer",
        "role": "admin",
        "phone": "+91 9876543210"
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "email": "driver1@wasteflow.io",
        "full_name": "Rajesh Kumar (Truck 01)",
        "role": "driver",
        "phone": "+91 9876543211"
    },
    {
        "id": "33333333-3333-3333-3333-333333333333",
        "email": "driver2@wasteflow.io",
        "full_name": "Manoj Varma (Truck 02)",
        "role": "driver",
        "phone": "+91 9876543212"
    }
]

def seed_database(start_date_str="2025-06-01T08:00:00+00:00", history_hours=48):
    print("=" * 60)
    print("SEEDING WASTEFLOW DATABASE")
    print("=" * 60)
    
    # 0. Clear old telemetry
    print("[*] Purging previous telemetry and collections...")
    db.clear_telemetry_and_collections()

    # 1. Seed Bins
    print(f"[*] Upserting {len(MOCK_BINS)} smart bins...")
    db.upsert_bins(MOCK_BINS)
    print("[+] Bins seeded successfully.")

    # 2. Seed Profiles
    print(f"[*] Upserting {len(MOCK_PROFILES)} user profiles...")
    db.upsert_profiles(MOCK_PROFILES)
    print("[+] Profiles seeded successfully.")

    # 3. Seed Simulation State
    print(f"[*] Initializing simulation virtual clock at {start_date_str}...")
    db.update_simulation_state(start_date_str, last_advance_hours=6)
    print("[+] Simulation state initialized.")

    # 4. Generate 48 hours of historical hourly telemetry ending at target levels
    print(f"[*] Generating {history_hours}h of historical telemetry for all bins...")
    start_dt = datetime.datetime.fromisoformat(start_date_str)
    telemetry_records = []

    for b in MOCK_BINS:
        b_id = b["id"]
        target_fill = float(b["current_fill_level_pct"])
        
        # Build 48 hourly readings backwards to simulate accumulation up to target_fill at start_dt
        hourly_history = []
        val = target_fill
        for h in range(0, history_hours + 1):
            t_dt = start_dt - datetime.timedelta(hours=h)
            sensor_val = min(100.0, max(5.0, val + random.gauss(0, b["sensor_noise_std_pct"] * 0.2)))
            hourly_history.append((t_dt, sensor_val))
            # Step backwards in time
            decrement = random.uniform(0.8, 2.0) * b["demand_multiplier"]
            val = max(10.0, val - decrement)

        # Append in chronological order
        for t_dt, sensor_val in reversed(hourly_history):
            telemetry_records.append({
                "bin_id": b_id,
                "timestamp": t_dt.isoformat(),
                "sensor_fill_level_pct": round(sensor_val, 2),
                "temperature_c": round(28.0 + random.uniform(-3, 3), 1),
                "humidity_pct": round(random.uniform(65.0, 85.0), 1),
                "rainfall_mm": 0.0 if random.random() > 0.15 else round(random.uniform(1.0, 15.0), 1),
                "is_holiday": 1 if t_dt.weekday() == 6 else 0,
                "local_event": 0,
                "sensor_anomaly": 0
            })

    inserted = db.insert_telemetry(telemetry_records)
    print(f"[+] Inserted {inserted} historical telemetry data points.")
    print("=" * 60)
    print("DATABASE SEED COMPLETED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    seed_database()
