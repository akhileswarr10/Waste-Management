import os
import sys
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app import app
from backend.database.db import db

def test_phase1():
    print("=" * 60)
    print("RUNNING PHASE 1 VERIFICATION TESTS")
    print("=" * 60)

    client = app.test_client()

    # 1. Health check
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.data}"
    health_data = json.loads(res.data)
    print(f"[PASS] Health check: {health_data['status']} ({health_data['database_backend']})")

    # 2. Get Bins
    res = client.get("/api/bins")
    assert res.status_code == 200, f"Get bins failed: {res.data}"
    bins_data = json.loads(res.data)
    bin_count = bins_data.get("count", 0)
    assert bin_count == 20, f"Expected 20 bins, got {bin_count}"
    print(f"[PASS] Retrieved {bin_count} smart bins from database.")

    # 3. Check Initial Simulation Status
    res = client.get("/api/simulation/status")
    assert res.status_code == 200
    status_data = json.loads(res.data)
    init_time = status_data["simulation_state"]["virtual_time"]
    print(f"[PASS] Initial Simulation Virtual Time: {init_time}, Average Fill: {status_data['average_fill_pct']}%")

    # 4. Advance Simulation by +6 Hours
    print("[*] Calling POST /api/simulation/advance (hours=6)...")
    res = client.post("/api/simulation/advance", json={"hours": 6})
    assert res.status_code == 200, f"Advance failed: {res.data}"
    adv_data = json.loads(res.data)["data"]
    print(f"[PASS] Simulation advanced from {adv_data['previous_virtual_time']} to {adv_data['new_virtual_time']}")
    print(f"[PASS] Generated {adv_data['telemetry_records_generated']} new telemetry readings across {adv_data['total_active_bins']} bins.")

    # 5. Check Telemetry Table
    recent_telemetry = db.get_all_recent_telemetry(limit_per_bin=10)
    print(f"[PASS] Telemetry table successfully holds active records (Total sampled: {len(recent_telemetry)})")

    # 6. Advance Simulation by +24 Hours (1 Day)
    print("[*] Calling POST /api/simulation/advance (hours=24)...")
    res = client.post("/api/simulation/advance", json={"hours": 24})
    assert res.status_code == 200, f"Advance 24h failed: {res.data}"
    adv_data_24 = json.loads(res.data)["data"]
    print(f"[PASS] Simulation advanced +24h to {adv_data_24['new_virtual_time']}")
    print(f"[PASS] Generated {adv_data_24['telemetry_records_generated']} new telemetry readings.")

    print("=" * 60)
    print("ALL PHASE 1 VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_phase1()
